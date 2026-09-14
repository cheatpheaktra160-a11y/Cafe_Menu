"""PHEAKTRA COFFEE Management System - Flask backend."""
from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
import base64
import csv
import io
import datetime
import json
import os
import secrets
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Use persistent disk on Render, fallback to local dir for development
DATA_DIR = os.environ.get("RENDER_DISK_PATH", BASE_DIR)
if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "cafe.db")
LOW_STOCK_THRESHOLD = 5

CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
    "EGP": "E\u00a3",
    "SAR": "SAR ",
    "AED": "AED ",
    "KWD": "KD ",
    "QAR": "QR ",
    "INR": "\u20b9",
    "JPY": "\u00a5",
    "TRY": "\u20ba",
    "BRL": "R$",
    "CAD": "C$",
    "AUD": "A$",
    "KHR": "៛",
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cafeshop-secret-key-2026")


@app.route("/favicon.ico")
def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%23f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8h1a4 4 0 1 1 0 8h-1"></path><path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"></path><line x1="6" y1="2" x2="6" y2="4"></line><line x1="10" y1="2" x2="10" y2="4"></line><line x1="14" y1="2" x2="14" y2="4"></line></svg>'
    return Response(svg, mimetype="image/svg+xml")

# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Cashier',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    image_url TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    is_featured INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    notes TEXT,
    points INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cafe_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_number INTEGER NOT NULL UNIQUE,
    qr_code TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Available',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    total REAL NOT NULL,
    paid_amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    cashier_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Paid',
    order_number TEXT DEFAULT '',
    table_id INTEGER,
    customer_name TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    order_status TEXT DEFAULT 'Pending',
    payment_status TEXT DEFAULT 'Unpaid',
    order_type TEXT DEFAULT 'Dine-In',
    tax_amount REAL DEFAULT 0,
    points_earned INTEGER DEFAULT 0,
    points_redeemed INTEGER DEFAULT 0,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(cashier_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount REAL NOT NULL DEFAULT 0,
    options TEXT DEFAULT '',
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT NOT NULL,
    brand TEXT,
    currency TEXT DEFAULT 'USD',
    timezone TEXT DEFAULT 'UTC',
    store_address TEXT DEFAULT 'Duem Mean coffee Takhmau',
    store_phone TEXT DEFAULT '(+885) 71 3030 308',
    wifi_ssid TEXT DEFAULT 'Pheaktra_Coffee_5G',
    wifi_password TEXT DEFAULT 'coffee2026',
    tax_rate REAL DEFAULT 0.0,
    receipt_footer TEXT DEFAULT 'Thank you for visiting! Savor every sip.'
);
"""

# (name, category index, price, stock, description, image, tags, is_featured)
SEED_PRODUCTS = [
    ("Americano", 0, 3.5, 30, "Classic espresso with hot water.", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80", "No ice, Light sugar", 1),
    ("Latte", 0, 4.2, 24, "Creamy latte with steamed milk.", "https://images.unsplash.com/photo-1534778101976-62847782c213?auto=format&fit=crop&w=800&q=80", "Less sugar, Extra shot", 1),
    ("Cappuccino", 0, 4.0, 22, "Double espresso topped with foamed milk.", "https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=800&q=80", "Extra foam", 0),
    ("Caramel Macchiato", 0, 4.8, 18, "Vanilla milk marked with espresso and caramel drizzle.", "https://images.unsplash.com/photo-1485808191679-5f86510681a2?auto=format&fit=crop&w=800&q=80", "Extra caramel", 1),
    ("Iced Coffee", 1, 3.8, 20, "Smooth cold brew iced coffee.", "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=800&q=80", "Ice, No sugar", 0),
    ("Cold Brew Classic", 1, 4.5, 15, "Slow-steeped 16 hour artisan cold brew.", "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=800&q=80", "Ice, Oat milk", 1),
    ("Hot Chocolate", 2, 4.0, 16, "Rich Belgian cocoa with steamed velvety milk.", "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?auto=format&fit=crop&w=800&q=80", "Whipped cream", 0),
    ("Green Tea Matcha", 3, 2.8, 40, "Light and calming Japanese green tea matcha.", "https://images.unsplash.com/photo-1627435601361-ec25f5b1d0e5?auto=format&fit=crop&w=800&q=80", "Honey, Lemon", 0),
    ("English Breakfast", 3, 2.8, 35, "Full-bodied black tea.", "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=800&q=80", "Milk, Sugar", 0),
    ("Butter Croissant", 4, 3.2, 12, "Flaky French butter croissant baked fresh daily.", "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=800&q=80", "Warmed", 1),
    ("Chocolate Muffin", 4, 3.4, 10, "Double chocolate muffin with melted chocolate chips.", "https://images.unsplash.com/photo-1607958996333-41aef7caefaa?auto=format&fit=crop&w=800&q=80", "Extra chips", 0),
    ("Club Sandwich", 5, 6.5, 8, "Turkey, bacon, lettuce and tomato stack with garlic aioli.", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=800&q=80", "No onion", 0),
]

SEED_CATEGORIES = ["Espresso", "Cold Brew", "Hot Chocolate", "Tea", "Pastries", "Snacks"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    db.close()
    return (rv[0] if rv else None) if one else rv


def table_columns(db, table):
    return [row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]


def format_date(dt=None):
    if dt is None:
        dt = datetime.datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_customer_tier(spent):
    spent = float(spent or 0)
    if spent >= 300:
        return "Platinum"
    if spent >= 150:
        return "Gold"
    if spent >= 50:
        return "Silver"
    return "Bronze"


def init_db():
    """Create/upgrade the schema and seed a brand-new database (idempotent)."""
    fresh = not os.path.exists(DB_PATH)
    with get_db() as db:
        db.executescript(SCHEMA)

        # Lightweight schema migrations for existing databases
        prod_cols = table_columns(db, "products")
        if "image_url" not in prod_cols:
            db.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
        if "tags" not in prod_cols:
            db.execute("ALTER TABLE products ADD COLUMN tags TEXT DEFAULT ''")
        if "is_featured" not in prod_cols:
            db.execute("ALTER TABLE products ADD COLUMN is_featured INTEGER NOT NULL DEFAULT 0")

        if "options" not in table_columns(db, "order_items"):
            db.execute("ALTER TABLE order_items ADD COLUMN options TEXT DEFAULT ''")

        if "points" not in table_columns(db, "customers"):
            db.execute("ALTER TABLE customers ADD COLUMN points INTEGER NOT NULL DEFAULT 0")

        order_cols = table_columns(db, "orders")
        if "status" not in order_cols:
            db.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'Paid'")
        
        for col, col_type, default_val in [
            ("table_id", "INTEGER", "NULL"),
            ("order_number", "TEXT", "''"),
            ("customer_name", "TEXT", "''"),
            ("phone", "TEXT", "''"),
            ("notes", "TEXT", "''"),
            ("order_status", "TEXT", "'Pending'"),
            ("payment_status", "TEXT", "'Unpaid'"),
            ("order_type", "TEXT", "'Dine-In'"),
            ("tax_amount", "REAL", "0"),
            ("points_earned", "INTEGER", "0"),
            ("points_redeemed", "INTEGER", "0"),
        ]:
            if col not in order_cols:
                db.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type} DEFAULT {default_val}")

        settings_cols = table_columns(db, "settings")
        for col, col_type, default_val in [
            ("store_address", "TEXT", "'Duem Mean coffee Takhmau'"),
            ("store_phone", "TEXT", "'(+885) 71 3030 308'"),
            ("wifi_ssid", "TEXT", "'Pheaktra_Coffee_5G'"),
            ("wifi_password", "TEXT", "'coffee2026'"),
            ("tax_rate", "REAL", "0.0"),
            ("receipt_footer", "TEXT", "'Thank you for visiting! Savor every sip.'"),
        ]:
            if col not in settings_cols:
                db.execute(f"ALTER TABLE settings ADD COLUMN {col} {col_type} DEFAULT {default_val}")

        # Seed reference categories
        for idx, name in enumerate(SEED_CATEGORIES):
            exists = db.execute(
                "SELECT 1 FROM categories WHERE name = ?", (name,)
            ).fetchone()
            if not exists:
                db.execute("INSERT INTO categories (name) VALUES (?)", (name,))

        # Seed sample tables
        for table_number in range(1, 9):
            qr_code = f"CAF-TABLE-{table_number:02d}"
            exists = db.execute(
                "SELECT 1 FROM cafe_tables WHERE table_number = ?", (table_number,)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO cafe_tables (table_number, qr_code, is_active, status, created_at) VALUES (?, ?, 1, 'Available', ?)",
                    (table_number, qr_code, format_date()),
                )

        # Seed products
        for name, cat_idx, price, stock, description, image, tags, is_featured in SEED_PRODUCTS:
            exists = db.execute(
                "SELECT id, image_url FROM products WHERE name = ?", (name,)
            ).fetchone()
            if not exists:
                category = db.execute(
                    "SELECT id FROM categories WHERE name = ?",
                    (SEED_CATEGORIES[cat_idx],),
                ).fetchone()
                db.execute(
                    "INSERT INTO products (name, category_id, price, stock, description,"
                    " image_url, tags, is_featured) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, category["id"], price, stock, description, image, tags, is_featured),
                )
            elif not exists["image_url"]:
                db.execute(
                    "UPDATE products SET image_url = ?, tags = ?, is_featured = ? WHERE id = ?",
                    (image, tags, is_featured, exists["id"]),
                )

        if fresh:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "Admin"),
            )
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("cashier", generate_password_hash("cashier123"), "Cashier"),
            )
            db.execute(
                "INSERT INTO settings (store_name, brand, currency, timezone, store_address, store_phone, wifi_ssid, wifi_password, tax_rate, receipt_footer) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("PHEAKTRA COFFEE", "PHEAKTRA COFFEE", "USD", "UTC", "Duem Mean coffee Takhmau", "(+885) 71 3030 308", "Pheaktra_Coffee_5G", "coffee2026", 0.0, "Thank you for visiting! Savor every sip."),
            )
        db.commit()


# ---------------------------------------------------------------------------
# Auth, roles and request guards
# ---------------------------------------------------------------------------
@app.before_request
def ensure_session_and_user():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            "SELECT * FROM users WHERE id = ? AND active = 1", (user_id,)
        ).fetchone()
        db.close()
        if g.user is None:
            session.clear()


@app.before_request
def csrf_protect():
    if request.method != "POST":
        return

    # Public login & API endpoints have tailored security handling
    if request.endpoint in ("login",) or request.path.startswith("/api/"):
        return

    sent = request.form.get("csrf_token", "") or request.headers.get("X-CSRFToken", "")
    if not sent or not secrets.compare_digest(sent, session.get("csrf_token", "")):
        abort(400, description="Invalid or missing CSRF token.")


def login_required(view):
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


def admin_required(view):
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        if g.user["role"] != "Admin":
            abort(403)
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def get_setting():
    """Return store settings, cached on g for the duration of the request."""
    if not hasattr(g, "_cached_setting"):
        g._cached_setting = query_db("SELECT * FROM settings ORDER BY id DESC LIMIT 1", one=True)
    return g._cached_setting


def currency_symbol():
    setting = get_setting()
    code = (setting["currency"] if setting else "USD") or "USD"
    return CURRENCY_SYMBOLS.get(code, f"{code} ")


def parse_float(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number else default


def parse_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def parse_cart(cart_json):
    """Validate the client cart, dropping malformed entries."""
    items = []
    try:
        data = json.loads(cart_json)
        for item in data:
            quantity = int(item.get("quantity", 0))
            if quantity <= 0:
                continue
            items.append({
                "product_id": int(item["product_id"]),
                "quantity": clamp(quantity, 1, 999),
                "discount": max(parse_float(item.get("discount", 0)), 0),
                "options": str(item.get("options", ""))[:200],
                "name": str(item.get("name", "")),
            })
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError):
        pass
    return items


def get_session_cart():
    cart = session.get("cart", [])
    if not isinstance(cart, list):
        cart = []
    cleaned = []
    for entry in cart:
        if not isinstance(entry, dict):
            continue
        try:
            product_id = int(entry.get("product_id"))
        except (TypeError, ValueError):
            continue
        quantity = max(int(entry.get("quantity", 1)), 1)
        cleaned.append({
            "product_id": product_id,
            "quantity": quantity,
            "size": str(entry.get("size", "")).strip(),
            "sugar": str(entry.get("sugar", "")).strip(),
            "ice": str(entry.get("ice", "")).strip(),
            "note": str(entry.get("note", "")).strip()[:200],
        })
    session["cart"] = cleaned
    return cleaned


def cart_summary(db=None):
    cart = get_session_cart()
    if not cart:
        return [], 0.0
    if db is None:
        db = get_db()
        close_db = True
    else:
        close_db = False
    ids = [item["product_id"] for item in cart]
    placeholders = ",".join("?" * len(ids))
    rows = db.execute(
        f"SELECT id, name, price, stock FROM products WHERE id IN ({placeholders})",
        ids,
    ).fetchall()
    catalog = {row["id"]: row for row in rows}
    items = []
    subtotal = 0.0
    for entry in cart:
        product = catalog.get(entry["product_id"])
        if product is None:
            continue
        quantity = max(int(entry.get("quantity", 1)), 1)
        unit_price = float(product["price"])
        total = unit_price * quantity
        details = []
        for key in ("size", "sugar", "ice"):
            value = entry.get(key, "")
            if value:
                details.append(value)
        if entry.get("note"):
            details.append(f"Note: {entry['note']}")
        summary = ", ".join(details) if details else "Standard"
        items.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": unit_price,
            "quantity": quantity,
            "line_total": round(total, 2),
            "options": summary,
            "stock": product["stock"],
        })
        subtotal += total
    if close_db:
        db.close()
    return items, round(subtotal, 2)


def generate_order_number():
    today = datetime.datetime.utcnow().strftime("%Y%m%d")
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) AS count FROM orders WHERE created_at LIKE ?",
        (f"{datetime.datetime.utcnow().strftime('%Y-%m-%d')}%",),
    ).fetchone()["count"]
    db.close()
    return f"CAF-{today}-{count + 1:03d}"


def generate_qr_data_url(code_text):
    """Generate base64 QR code PNG string."""
    try:
        import qrcode
        img = qrcode.make(code_text)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        # Quick fallback QR API URL if qrcode lib fails
        return f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={code_text}"


@app.context_processor
def inject_globals():
    setting = get_setting()
    symbol = CURRENCY_SYMBOLS.get((setting["currency"] if setting else "USD") or "USD", "$")

    def money(value):
        try:
            return f"{symbol}{float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return f"{symbol}0.00"

    cart = get_session_cart()
    total_cart_count = sum(item.get("quantity", 1) for item in cart)

    # Kitchen pending count for staff badge
    active_kitchen_count = 0
    if g.user:
        try:
            db = get_db()
            active_kitchen_count = db.execute(
                "SELECT COUNT(*) AS count FROM orders WHERE status != 'Voided' AND order_status IN ('Pending', 'Preparing')"
            ).fetchone()["count"]
            db.close()
        except Exception:
            active_kitchen_count = 0

    return {
        "current_user": g.user,
        "setting": setting,
        "currency_symbol": symbol,
        "money": money,
        "csrf_token": lambda: session.get("csrf_token", ""),
        "is_admin": bool(g.user and g.user["role"] == "Admin"),
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "cart_count": total_cart_count,
        "session_table_id": session.get("table_id"),
        "session_table_number": session.get("table_number"),
        "active_kitchen_count": active_kitchen_count,
        "get_customer_tier": get_customer_tier,
    }


# ---------------------------------------------------------------------------
# Public & customer routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("menu"))


@app.route("/home")
def landing_home():
    if g.user:
        return redirect(url_for("dashboard"))
    featured = query_db(
        "SELECT p.*, c.name AS category_name FROM products p "
        "JOIN categories c ON c.id = p.category_id WHERE p.stock > 0 "
        "ORDER BY p.is_featured DESC, p.id ASC LIMIT 8"
    )
    categories = query_db("SELECT * FROM categories ORDER BY name")
    return render_template("public_home.html", title="Home", featured=featured, categories=categories)


@app.route("/menu", methods=["GET", "POST"])
def menu():
    if request.method == "POST":
        product_id = parse_int(request.form.get("product_id"))
        quantity = max(parse_int(request.form.get("quantity"), 1), 1)
        if product_id <= 0:
            flash("Please select a valid product.", "error")
            return redirect(url_for("menu"))
        product = query_db(
            "SELECT * FROM products WHERE id = ? AND stock > 0", (product_id,), one=True
        )
        if not product:
            flash("This item is unavailable right now.", "error")
            return redirect(url_for("menu"))
        cart = get_session_cart()
        entry = {
            "product_id": product_id,
            "quantity": quantity,
            "size": request.form.get("size", "").strip(),
            "sugar": request.form.get("sugar", "").strip(),
            "ice": request.form.get("ice", "").strip(),
            "note": request.form.get("note", "").strip()[:200],
        }
        existing = None
        for item in cart:
            if (
                item["product_id"] == product_id
                and item["size"] == entry["size"]
                and item["sugar"] == entry["sugar"]
                and item["ice"] == entry["ice"]
                and item["note"] == entry["note"]
            ):
                existing = item
                break
        if existing is not None:
            existing["quantity"] += quantity
        else:
            cart.append(entry)
        session["cart"] = cart
        flash(f"{product['name']} added to your cart.", "success")
        return redirect(url_for("menu"))

    category_id = parse_int(request.args.get("category_id"))
    search = request.args.get("search", "").strip()
    query = (
        "SELECT p.*, c.name AS category_name FROM products p "
        "JOIN categories c ON c.id = p.category_id WHERE p.stock > 0"
    )
    params = []
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ? OR p.tags LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    query += " ORDER BY p.is_featured DESC, p.name ASC"
    items = query_db(query, params)
    categories = query_db("SELECT * FROM categories ORDER BY name")
    return render_template(
        "public_menu.html",
        title="Menu",
        menu_items=items,
        categories=categories,
        selected_category=category_id,
        search=search,
    )


@app.route("/menu/<int:product_id>")
def product_detail(product_id):
    product = query_db(
        "SELECT p.*, c.name AS category_name FROM products p "
        "JOIN categories c ON c.id = p.category_id WHERE p.id = ?",
        (product_id,),
        one=True,
    )
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("menu"))
    return render_template("public_product.html", title=product["name"], product=product)


@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        action = request.form.get("action")
        cart_items = get_session_cart()
        if action == "remove":
            product_id = parse_int(request.form.get("product_id"))
            size = request.form.get("size", "")
            sugar = request.form.get("sugar", "")
            ice = request.form.get("ice", "")
            note = request.form.get("note", "")
            cart_items = [
                item for item in cart_items
                if not (
                    item["product_id"] == product_id
                    and item["size"] == size
                    and item["sugar"] == sugar
                    and item["ice"] == ice
                    and item["note"] == note
                )
            ]
            session["cart"] = cart_items
            flash("Item removed from cart.", "success")
        elif action == "update":
            product_id = parse_int(request.form.get("product_id"))
            quantity = max(parse_int(request.form.get("quantity"), 1), 1)
            for item in cart_items:
                if item["product_id"] == product_id:
                    item["quantity"] = quantity
                    break
            session["cart"] = cart_items
            flash("Cart updated.", "success")
        return redirect(url_for("cart"))

    items, subtotal = cart_summary()
    return render_template("public_cart.html", title="Cart", cart_items=items, subtotal=subtotal)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_items, subtotal = cart_summary()
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("menu"))
    tables = query_db("SELECT * FROM cafe_tables WHERE is_active = 1 ORDER BY table_number")
    setting = get_setting()
    tax_rate = float(setting["tax_rate"]) if setting and setting["tax_rate"] else 0.0
    tax_amount = round(subtotal * (tax_rate / 100.0), 2)
    grand_total = round(subtotal + tax_amount, 2)

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        note = request.form.get("notes", "").strip()[:200]
        selected_table = parse_int(request.form.get("table_id"))
        order_type = "Dine-In" if selected_table else "Takeaway"
        if not customer_name:
            flash("Please enter your name before checkout.", "error")
            return render_template(
                "public_checkout.html",
                title="Checkout",
                cart_items=cart_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                grand_total=grand_total,
                tables=tables,
                selected_table=selected_table,
            )
        db = get_db()
        default_cashier = db.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        cashier_id = g.user["id"] if g.user else (default_cashier["id"] if default_cashier else 1)
        with db:
            order_number = generate_order_number()
            # If customer exists by phone or name, link customer
            existing_cust = None
            if phone:
                existing_cust = db.execute("SELECT id FROM customers WHERE phone = ?", (phone,)).fetchone()
            if not existing_cust and customer_name:
                existing_cust = db.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()
            
            cust_id = existing_cust["id"] if existing_cust else None
            points_earned = int(grand_total)
            if cust_id:
                db.execute("UPDATE customers SET points = points + ? WHERE id = ?", (points_earned, cust_id))

            cursor = db.execute(
                "INSERT INTO orders (customer_id, customer_name, phone, notes, table_id, total, paid_amount, payment_method, discount, created_at, cashier_id, status, order_status, payment_status, order_number, order_type, tax_amount, points_earned) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'Cash', 0, ?, ?, 'Pending', 'Pending', 'Unpaid', ?, ?, ?, ?)",
                (cust_id, customer_name, phone or None, note, selected_table or None, grand_total, grand_total, format_date(), cashier_id, order_number, order_type, tax_amount, points_earned),
            )
            order_id = cursor.lastrowid
            for item in cart_items:
                product = db.execute(
                    "SELECT * FROM products WHERE id = ?", (item["product_id"],)
                ).fetchone()
                if not product:
                    continue
                db.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, options) VALUES (?, ?, ?, ?, 0, ?)",
                    (order_id, item["product_id"], item["quantity"], item["price"], item["options"]),
                )
                db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item["quantity"], item["product_id"]),
                )
        db.close()
        session["cart"] = []
        flash(f"Order {order_number} has been placed successfully!", "success")
        return redirect(url_for("track_order", q=order_number))

    return render_template(
        "public_checkout.html",
        title="Checkout",
        cart_items=cart_items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        grand_total=grand_total,
        tables=tables,
    )


@app.route("/track", methods=["GET", "POST"])
def track_order():
    q = (request.args.get("q") or request.form.get("search") or "").strip()
    if request.method == "POST" and q:
        return redirect(url_for("track_order", q=q))
    if not q:
        return render_template("public_track.html", title="Track Order", search=q, order=None)
    order = query_db(
        "SELECT o.*, t.table_number FROM orders o LEFT JOIN cafe_tables t ON t.id = o.table_id WHERE o.order_number = ? OR o.customer_name LIKE ? ORDER BY o.created_at DESC LIMIT 1",
        (q, f"%{q}%"),
        one=True,
    )
    if order:
        items = query_db(
            "SELECT oi.*, p.name AS product_name FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?",
            (order["id"],),
        )
        return render_template("public_track.html", title="Track Order", search=q, order=order, items=items)
    flash("No matching order was found. Please check your order number.", "error")
    return render_template("public_track.html", title="Track Order", search=q, order=None)


@app.route("/qr/<string:qr_code>")
def qr_table_order(qr_code):
    table = query_db("SELECT * FROM cafe_tables WHERE qr_code = ?", (qr_code,), one=True)
    if not table:
        flash("This QR table code is invalid.", "error")
        return redirect(url_for("home"))
    session["table_id"] = table["id"]
    session["table_number"] = table["table_number"]
    flash(f"Welcome! You are ordering for Table {table['table_number']}.", "success")
    return redirect(url_for("menu", category_id=""))


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = query_db(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,), one=True
        )
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["csrf_token"] = secrets.token_hex(32)
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", title="Login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    now = datetime.datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    week_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    db = get_db()
    stats = db.execute(
        "SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS revenue,"
        " COALESCE(SUM(discount), 0) AS discounts FROM orders"
        " WHERE created_at LIKE ? AND status != 'Voided'",
        (f"{today}%",),
    ).fetchone()
    weekly = db.execute(
        "SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS revenue FROM orders"
        " WHERE created_at >= ? AND status != 'Voided'",
        (week_ago,),
    ).fetchone()
    monthly = db.execute(
        "SELECT COUNT(*) AS order_count, COALESCE(SUM(total), 0) AS revenue FROM orders"
        " WHERE created_at >= ? AND status != 'Voided'",
        (month_ago,),
    ).fetchone()
    expense_total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS expense_total FROM expenses WHERE created_at LIKE ?",
        (f"{today}%",),
    ).fetchone()["expense_total"]
    product_count = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
    categories = db.execute("SELECT COUNT(*) AS count FROM categories").fetchone()["count"]

    recent_orders = db.execute(
        ORDERS_SELECT + " ORDER BY orders.created_at DESC, orders.id DESC LIMIT 8"
    ).fetchall()

    low_stock = db.execute(
        "SELECT id, name, stock FROM products WHERE stock <= ? ORDER BY stock ASC LIMIT 8",
        (LOW_STOCK_THRESHOLD,),
    ).fetchall()

    top_products = db.execute(
        "SELECT p.name, SUM(oi.quantity) AS qty,"
        " SUM(oi.quantity * oi.unit_price - COALESCE(oi.discount, 0)) AS revenue"
        " FROM order_items oi"
        " JOIN orders o ON o.id = oi.order_id"
        " JOIN products p ON p.id = oi.product_id"
        " WHERE o.status != 'Voided' AND o.created_at >= ?"
        " GROUP BY p.id ORDER BY qty DESC LIMIT 5",
        (month_ago,),
    ).fetchall()

    active_tables_count = db.execute(
        "SELECT COUNT(DISTINCT table_id) AS count FROM orders WHERE status != 'Voided' AND order_status IN ('Pending', 'Preparing') AND table_id IS NOT NULL"
    ).fetchone()["count"]

    db.close()

    return render_template(
        "dashboard.html",
        title="Dashboard",
        stats=stats,
        orders=recent_orders,
        weekly=weekly,
        monthly=monthly,
        expense_total=expense_total,
        products_count=product_count,
        categories_count=categories,
        low_stock=low_stock,
        top_products=top_products,
        active_tables_count=active_tables_count,
    )


# ---------------------------------------------------------------------------
# Kitchen Display System (KDS / Barista View)
# ---------------------------------------------------------------------------
@app.route("/kds")
@login_required
def kds():
    db = get_db()
    # Fetch all orders not completed/voided or completed in the last 15 minutes
    active_orders = db.execute(
        "SELECT orders.*, customers.name AS customer_full_name, cafe_tables.table_number "
        "FROM orders "
        "LEFT JOIN customers ON orders.customer_id = customers.id "
        "LEFT JOIN cafe_tables ON orders.table_id = cafe_tables.id "
        "WHERE orders.status != 'Voided' AND orders.order_status IN ('Pending', 'Preparing', 'Ready') "
        "ORDER BY CASE orders.order_status "
        "  WHEN 'Pending' THEN 1 "
        "  WHEN 'Preparing' THEN 2 "
        "  WHEN 'Ready' THEN 3 "
        "  ELSE 4 END, orders.created_at ASC"
    ).fetchall()

    # Get items for each order
    orders_with_items = []
    for order in active_orders:
        items = db.execute(
            "SELECT oi.*, p.name AS product_name, p.image_url FROM order_items oi "
            "JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?",
            (order["id"],),
        ).fetchall()
        orders_with_items.append({"order": order, "items": items})

    completed_recent = db.execute(
        "SELECT orders.*, customers.name AS customer_full_name, cafe_tables.table_number "
        "FROM orders "
        "LEFT JOIN customers ON orders.customer_id = customers.id "
        "LEFT JOIN cafe_tables ON orders.table_id = cafe_tables.id "
        "WHERE orders.status != 'Voided' AND orders.order_status = 'Completed' "
        "ORDER BY orders.created_at DESC LIMIT 8"
    ).fetchall()

    db.close()
    return render_template(
        "kds.html",
        title="Kitchen Display System",
        orders_with_items=orders_with_items,
        completed_recent=completed_recent,
    )


# ---------------------------------------------------------------------------
# Point of sale
# ---------------------------------------------------------------------------
@app.route("/pos", methods=["GET", "POST"])
@login_required
def pos():
    db = get_db()
    setting = get_setting()
    tax_rate = float(setting["tax_rate"]) if setting and setting["tax_rate"] else 0.0

    if request.method == "POST":
        items = parse_cart(request.form.get("cart_data", "[]"))
        if not items:
            db.close()
            flash("Please add items to the cart before completing the sale.", "error")
            return redirect(url_for("pos"))

        ids = [item["product_id"] for item in items]
        placeholders = ",".join("?" * len(ids))
        rows = db.execute(
            f"SELECT id, name, price, stock FROM products WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        catalog = {row["id"]: row for row in rows}

        problems = []
        sellable = []
        for item in items:
            product = catalog.get(item["product_id"])
            if product is None:
                problems.append(f"Unknown product #{item['product_id']} was removed.")
                continue
            if item["quantity"] > product["stock"]:
                problems.append(
                    f"Not enough stock for {product['name']} (available: {product['stock']})."
                )
                continue
            item["unit_price"] = float(product["price"])
            item["discount"] = clamp(item["discount"], 0, item["unit_price"] * item["quantity"])
            sellable.append(item)

        if problems:
            db.close()
            for problem in problems:
                flash(problem, "error")
            return redirect(url_for("pos"))

        subtotal = sum(i["unit_price"] * i["quantity"] - i["discount"] for i in sellable)
        order_discount = clamp(parse_float(request.form.get("order_discount", 0)), 0, subtotal)
        
        # Points redemption handling
        points_redeemed = parse_int(request.form.get("points_redeemed", 0))
        customer_id = parse_int(request.form.get("customer_id")) or None
        
        points_discount = 0.0
        if customer_id and points_redeemed > 0:
            cust = db.execute("SELECT points FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if cust and cust["points"] >= points_redeemed:
                # 20 points = $1.00 discount
                points_discount = round(points_redeemed / 20.0, 2)
                order_discount = min(subtotal, order_discount + points_discount)

        discounted_subtotal = max(0.0, subtotal - order_discount)
        tax_amount = round(discounted_subtotal * (tax_rate / 100.0), 2)
        total = round(discounted_subtotal + tax_amount, 2)

        paid_amount = round(max(parse_float(request.form.get("paid_amount")), total), 2)
        payment_method = request.form.get("payment_method", "Cash")
        if payment_method not in ("Cash", "Card", "QR"):
            payment_method = "Cash"

        order_type = request.form.get("order_type", "Dine-In")
        if order_type not in ("Dine-In", "Takeaway", "Delivery"):
            order_type = "Dine-In"

        table_id = parse_int(request.form.get("table_id")) if order_type == "Dine-In" else None
        order_number = generate_order_number()
        points_earned = int(total) if customer_id else 0

        with db:
            cursor = db.execute(
                "INSERT INTO orders (customer_id, customer_name, total, paid_amount, payment_method,"
                " discount, created_at, cashier_id, status, order_status, payment_status, order_number, table_id, order_type, tax_amount, points_earned, points_redeemed) "
                "VALUES (?, (SELECT name FROM customers WHERE id = ?), ?, ?, ?, ?, ?, ?, 'Paid', 'Pending', 'Paid', ?, ?, ?, ?, ?, ?)",
                (customer_id, customer_id, total, paid_amount, payment_method, order_discount,
                 format_date(), g.user["id"], order_number, table_id, order_type, tax_amount, points_earned, points_redeemed),
            )
            order_id = cursor.lastrowid
            
            # Update customer points
            if customer_id:
                db.execute(
                    "UPDATE customers SET points = points - ? + ? WHERE id = ?",
                    (points_redeemed, points_earned, customer_id),
                )

            for item in sellable:
                db.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price,"
                    " discount, options) VALUES (?, ?, ?, ?, ?, ?)",
                    (order_id, item["product_id"], item["quantity"], item["unit_price"],
                     item["discount"], item["options"]),
                )
                db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (item["quantity"], item["product_id"], item["quantity"]),
                )
        db.close()
        flash("Order completed successfully!", "success")
        return redirect(url_for("receipt", order_id=order_id))

    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    products = db.execute(
        "SELECT products.*, categories.name AS category_name FROM products"
        " JOIN categories ON products.category_id = categories.id ORDER BY products.is_featured DESC, products.name"
    ).fetchall()
    customers = db.execute("SELECT * FROM customers ORDER BY name").fetchall()
    tables = db.execute("SELECT * FROM cafe_tables WHERE is_active = 1 ORDER BY table_number").fetchall()
    db.close()
    return render_template(
        "pos.html",
        title="POS",
        categories=categories,
        products=products,
        customers=customers,
        tables=tables,
        tax_rate=tax_rate,
    )


# ---------------------------------------------------------------------------
# Receipts and orders
# ---------------------------------------------------------------------------
ORDERS_SELECT = (
    "SELECT orders.*, customers.name AS customer_name, users.username AS cashier_name, cafe_tables.table_number"
    " FROM orders LEFT JOIN customers ON orders.customer_id = customers.id"
    " LEFT JOIN users ON orders.cashier_id = users.id"
    " LEFT JOIN cafe_tables ON orders.table_id = cafe_tables.id"
)


@app.route("/receipt/<int:order_id>")
@login_required
def receipt(order_id):
    order = query_db(ORDERS_SELECT + " WHERE orders.id = ?", (order_id,), one=True)
    if not order:
        flash("Receipt not found.", "error")
        return redirect(url_for("orders"))
    items = query_db(
        "SELECT order_items.*, products.name AS product_name FROM order_items"
        " JOIN products ON order_items.product_id = products.id WHERE order_id = ?",
        (order_id,),
    )
    change_due = max(float(order["paid_amount"]) - float(order["total"]), 0)
    qr_url = generate_qr_data_url(order["order_number"] or f"CAF-{order['id']}")
    return render_template(
        "receipt.html",
        title=f"Receipt #{order['order_number'] or order['id']}",
        order=order,
        items=items,
        change_due=change_due,
        qr_url=qr_url,
    )


@app.route("/orders")
@login_required
def orders():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    query = ORDERS_SELECT + " WHERE 1=1"
    params = []
    if search:
        query += (" AND (CAST(orders.id AS TEXT) LIKE ? OR orders.order_number LIKE ?"
                  " OR customers.name LIKE ? OR orders.customer_name LIKE ?"
                  " OR users.username LIKE ?)")
        params.extend([f"%{search}%"] * 5)
    if status_filter:
        query += " AND (orders.order_status = ? OR orders.status = ?)"
        params.extend([status_filter, status_filter])
        
    query += " ORDER BY orders.created_at DESC, orders.id DESC LIMIT 150"
    rows = query_db(query, params)
    return render_template("orders.html", title="Orders", orders=rows, search=search, status_filter=status_filter)


@app.route("/orders/<int:order_id>/void", methods=["POST"])
@admin_required
def void_order(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order or order["status"] == "Voided":
        db.close()
        flash("Order cannot be voided or was already voided.", "error")
        return redirect(url_for("orders"))
    with db:
        db.execute("UPDATE orders SET status = 'Voided', order_status = 'Cancelled' WHERE id = ?", (order_id,))
        items = db.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        for item in items:
            db.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
        # Revert customer points
        if order["customer_id"]:
            db.execute(
                "UPDATE customers SET points = max(0, points - ? + ?) WHERE id = ?",
                (order["points_earned"], order["points_redeemed"], order["customer_id"]),
            )
    db.close()
    flash(f"Order #{order_id} has been voided and stock restored.", "success")
    return redirect(url_for("orders"))


@app.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    status = request.form.get("status", "").strip()
    allowed = ["Pending", "Preparing", "Ready", "Completed", "Cancelled"]
    if status not in allowed:
        flash("Invalid order status.", "error")
        return redirect(url_for("orders"))
    db = get_db()
    db.execute("UPDATE orders SET order_status = ?, status = ? WHERE id = ?", (status, status, order_id))
    db.commit()
    db.close()
    flash(f"Order #{order_id} marked as {status}.", "success")
    
    # Redirect back to where request originated (e.g. KDS or Orders)
    next_url = request.form.get("next") or request.referrer or url_for("orders")
    return redirect(next_url)


# ---------------------------------------------------------------------------
# Tables & QR stands
# ---------------------------------------------------------------------------
@app.route("/tables", methods=["GET", "POST"])
@admin_required
def tables():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_table":
            table_number = parse_int(request.form.get("table_number"))
            if table_number <= 0:
                flash("Table number must be greater than zero.", "error")
            else:
                qr_code = f"CAF-TABLE-{table_number:02d}"
                try:
                    db.execute(
                        "INSERT INTO cafe_tables (table_number, qr_code, is_active, status, created_at) VALUES (?, ?, 1, 'Available', ?)",
                        (table_number, qr_code, format_date()),
                    )
                    db.commit()
                    flash(f"Table {table_number} created.", "success")
                except sqlite3.IntegrityError:
                    flash(f"Table {table_number} already exists.", "error")
        elif action == "toggle_active":
            table_id = parse_int(request.form.get("table_id"))
            table = db.execute("SELECT * FROM cafe_tables WHERE id = ?", (table_id,)).fetchone()
            if table:
                db.execute(
                    "UPDATE cafe_tables SET is_active = ?, status = ? WHERE id = ?",
                    (0 if table["is_active"] else 1, 'Available' if (not table["is_active"]) else 'Unavailable', table_id),
                )
                db.commit()
                flash(f"Table {table['table_number']} updated.", "success")
        db.close()
        return redirect(url_for("tables"))

    rows = db.execute("SELECT * FROM cafe_tables ORDER BY table_number").fetchall()
    
    # Check table active orders
    occupied_tables = {
        r["table_id"] for r in db.execute(
            "SELECT DISTINCT table_id FROM orders WHERE status != 'Voided' AND order_status IN ('Pending', 'Preparing') AND table_id IS NOT NULL"
        ).fetchall()
    }
    
    qr_images = {}
    for row in rows:
        qr_images[row["id"]] = generate_qr_data_url(f"http://{request.host}/qr/{row['qr_code']}")
    db.close()
    return render_template(
        "tables.html",
        title="Tables",
        tables=rows,
        qr_images=qr_images,
        occupied_tables=occupied_tables,
    )


@app.route("/tables/print-all")
@admin_required
def print_all_tables():
    db = get_db()
    rows = db.execute("SELECT * FROM cafe_tables WHERE is_active = 1 ORDER BY table_number").fetchall()
    qr_images = {}
    for row in rows:
        qr_images[row["id"]] = generate_qr_data_url(f"http://{request.host}/qr/{row['qr_code']}")
    db.close()
    return render_template(
        "table_qr_print.html",
        title="Print Table QR Stands",
        tables=rows,
        qr_images=qr_images,
    )


@app.route("/tables/<int:table_id>/print")
@admin_required
def print_single_table(table_id):
    table = query_db("SELECT * FROM cafe_tables WHERE id = ?", (table_id,), one=True)
    if not table:
        flash("Table not found.", "error")
        return redirect(url_for("tables"))
    qr_images = {table["id"]: generate_qr_data_url(f"http://{request.host}/qr/{table['qr_code']}")}
    return render_template(
        "table_qr_print.html",
        title=f"Print QR Stand - Table {table['table_number']}",
        tables=[table],
        qr_images=qr_images,
    )


# ---------------------------------------------------------------------------
# Products and categories (admin)
# ---------------------------------------------------------------------------
@app.route("/products", methods=["GET", "POST"])
@admin_required
def products():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_category":
            name = request.form.get("category_name", "").strip()
            exists = db.execute(
                "SELECT 1 FROM categories WHERE name = ?", (name,)
            ).fetchone()
            if not name:
                flash("Category name is required.", "error")
            elif exists:
                flash(f"Category '{name}' already exists.", "error")
            else:
                try:
                    db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                    db.commit()
                    flash("Category added.", "success")
                except sqlite3.IntegrityError:
                    flash(f"Category '{name}' already exists.", "error")
        elif action == "delete_category":
            category_id = parse_int(request.form.get("category_id"))
            used = db.execute(
                "SELECT COUNT(*) AS count FROM products WHERE category_id = ?",
                (category_id,),
            ).fetchone()["count"]
            if used:
                flash("Move or delete this category's products first.", "error")
            else:
                db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                db.commit()
                flash("Category deleted.", "success")
        elif action in ("add_product", "update_product"):
            name = request.form.get("product_name", "").strip()
            category_id = parse_int(request.form.get("product_category"))
            price = round(parse_float(request.form.get("product_price")), 2)
            stock = max(parse_int(request.form.get("product_stock")), 0)
            description = request.form.get("product_description", "").strip()
            image = request.form.get("product_image", "").strip()
            tags = request.form.get("product_tags", "").strip()
            is_featured = 1 if request.form.get("is_featured") else 0
            if not name or not category_id or price <= 0:
                flash("Name, category and a positive price are required.", "error")
            elif action == "add_product":
                db.execute(
                    "INSERT INTO products (name, category_id, price, stock, description,"
                    " image_url, tags, is_featured) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, category_id, price, stock, description, image, tags, is_featured),
                )
                db.commit()
                flash("Product added.", "success")
            else:
                db.execute(
                    "UPDATE products SET name = ?, category_id = ?, price = ?, stock = ?,"
                    " description = ?, image_url = ?, tags = ?, is_featured = ? WHERE id = ?",
                    (name, category_id, price, stock, description, image, tags, is_featured,
                     parse_int(request.form.get("product_id"))),
                )
                db.commit()
                flash("Product updated.", "success")
        elif action == "delete_product":
            product_id = parse_int(request.form.get("product_id"))
            sold = db.execute(
                "SELECT COUNT(*) AS count FROM order_items WHERE product_id = ?",
                (product_id,),
            ).fetchone()["count"]
            if sold:
                flash(
                    "This product appears in past orders and cannot be deleted."
                    " Set its stock to 0 instead.",
                    "error",
                )
            else:
                db.execute("DELETE FROM products WHERE id = ?", (product_id,))
                db.commit()
                flash("Product deleted.", "success")
        db.close()
        return redirect(url_for("products"))

    edit_product = None
    edit_id = parse_int(request.args.get("edit"))
    if edit_id:
        edit_product = query_db("SELECT * FROM products WHERE id = ?", (edit_id,), one=True)

    categories = db.execute(
        "SELECT categories.*, COUNT(products.id) AS product_count FROM categories"
        " LEFT JOIN products ON products.category_id = categories.id"
        " GROUP BY categories.id ORDER BY categories.name"
    ).fetchall()
    rows = db.execute(
        "SELECT products.*, categories.name AS category_name FROM products"
        " JOIN categories ON products.category_id = categories.id ORDER BY products.name"
    ).fetchall()
    db.close()

    setting = get_setting()
    low_stock_threshold = parse_int(setting["low_stock_threshold"] if setting and "low_stock_threshold" in setting.keys() else 15, default=15)

    total_products = len(rows)
    total_categories = len(categories)
    featured_count = sum(1 for p in rows if p["is_featured"])
    low_stock_count = sum(1 for p in rows if 0 < p["stock"] <= low_stock_threshold)
    out_of_stock_count = sum(1 for p in rows if p["stock"] <= 0)
    total_val = sum(p["price"] * p["stock"] for p in rows)

    stats = {
        "total_products": total_products,
        "total_categories": total_categories,
        "featured": featured_count,
        "low_stock": low_stock_count,
        "out_of_stock": out_of_stock_count,
        "total_value": total_val,
    }

    return render_template(
        "products.html",
        title="Products",
        categories=categories,
        products=rows,
        edit_product=edit_product,
        stats=stats,
        low_stock_threshold=low_stock_threshold,
    )


# ---------------------------------------------------------------------------
# Inventory (admin)
# ---------------------------------------------------------------------------
@app.route("/inventory", methods=["GET", "POST"])
@admin_required
def inventory():
    db = get_db()
    if request.method == "POST":
        product_id = parse_int(request.form.get("product_id"))
        new_stock = max(parse_int(request.form.get("stock")), 0)
        db.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        db.commit()
        flash("Stock updated.", "success")
        db.close()
        return redirect(url_for("inventory"))

    rows = db.execute(
        "SELECT products.*, categories.name AS category_name FROM products"
        " JOIN categories ON products.category_id = categories.id ORDER BY products.name"
    ).fetchall()
    stats = {
        "total_items": len(rows),
        "items_count": len(rows),
        "items": len(rows),
        "low": sum(1 for r in rows if 0 < r["stock"] <= LOW_STOCK_THRESHOLD),
        "out": sum(1 for r in rows if r["stock"] <= 0),
        "value": sum(r["stock"] * r["price"] for r in rows),
    }
    db.close()
    return render_template("inventory.html", title="Inventory", products=rows, stats=stats)


# ---------------------------------------------------------------------------
# Customers & Loyalty
# ---------------------------------------------------------------------------
@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action", "create")
        name = request.form.get("customer_name", "").strip()
        if action == "delete":
            if not (g.user and g.user["role"] == "Admin"):
                abort(403)
            customer_id = parse_int(request.form.get("customer_id"))
            with db:
                db.execute(
                    "UPDATE orders SET customer_id = NULL WHERE customer_id = ?",
                    (customer_id,),
                )
                db.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            db.commit()
            flash("Customer deleted.", "success")
        elif not name:
            flash("Customer name is required.", "error")
        elif action == "create":
            db.execute(
                "INSERT INTO customers (name, phone, email, notes, points) VALUES (?, ?, ?, ?, ?)",
                (name,
                 request.form.get("customer_phone", "").strip(),
                 request.form.get("customer_email", "").strip(),
                 request.form.get("customer_notes", "").strip(),
                 parse_int(request.form.get("customer_points", 0))),
            )
            db.commit()
            flash("Customer saved.", "success")
        elif action == "update":
            db.execute(
                "UPDATE customers SET name = ?, phone = ?, email = ?, notes = ?, points = ? WHERE id = ?",
                (name,
                 request.form.get("customer_phone", "").strip(),
                 request.form.get("customer_email", "").strip(),
                 request.form.get("customer_notes", "").strip(),
                 parse_int(request.form.get("customer_points", 0)),
                 parse_int(request.form.get("customer_id"))),
            )
            db.commit()
            flash("Customer updated.", "success")
        db.close()
        return redirect(url_for("customers"))

    edit_customer = None
    edit_id = parse_int(request.args.get("edit"))
    if edit_id:
        edit_customer = query_db("SELECT * FROM customers WHERE id = ?", (edit_id,), one=True)

    rows = db.execute(
        "SELECT customers.*, COUNT(orders.id) AS order_count,"
        " COALESCE(SUM(CASE WHEN orders.status != 'Voided' THEN orders.total ELSE 0 END), 0) AS spent"
        " FROM customers LEFT JOIN orders ON orders.customer_id = customers.id"
        " GROUP BY customers.id ORDER BY spent DESC, customers.name ASC"
    ).fetchall()
    db.close()
    return render_template(
        "customers.html",
        title="Customers & Loyalty",
        customers=rows,
        edit_customer=edit_customer,
    )


# ---------------------------------------------------------------------------
# Expenses (admin)
# ---------------------------------------------------------------------------
@app.route("/expenses", methods=["GET", "POST"])
@admin_required
def expenses():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action", "create")
        if action == "delete":
            db.execute(
                "DELETE FROM expenses WHERE id = ?", (parse_int(request.form.get("expense_id")),)
            )
            db.commit()
            flash("Expense deleted.", "success")
        else:
            title = request.form.get("expense_title", "").strip()
            amount = round(parse_float(request.form.get("expense_amount")), 2)
            category = request.form.get("expense_category", "").strip() or "General"
            note = request.form.get("expense_note", "").strip()
            if title and amount > 0:
                db.execute(
                    "INSERT INTO expenses (title, amount, category, note, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (title, amount, category, note, format_date()),
                )
                db.commit()
                flash("Expense recorded.", "success")
            else:
                flash("Title and a positive amount are required.", "error")
        db.close()
        return redirect(url_for("expenses"))

    rows = db.execute(
        "SELECT * FROM expenses ORDER BY created_at DESC, id DESC LIMIT 100"
    ).fetchall()
    month_total = query_db(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE created_at >= ?",
        ((datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),),
        one=True,
    )["total"]
    db.close()
    return render_template(
        "expenses.html", title="Expenses", expenses=rows, month_total=month_total
    )


# ---------------------------------------------------------------------------
# Settings and account
# ---------------------------------------------------------------------------
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    db = get_db()
    setting = db.execute("SELECT * FROM settings ORDER BY id DESC LIMIT 1").fetchone()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "store_settings":
            if g.user["role"] != "Admin":
                db.close()
                abort(403)
            store_name = request.form.get("store_name", "").strip()
            brand = request.form.get("brand", "").strip()
            currency = request.form.get("currency", "USD").strip().upper()
            timezone = request.form.get("timezone", "UTC").strip() or "UTC"
            store_address = request.form.get("store_address", "").strip()
            store_phone = request.form.get("store_phone", "").strip()
            wifi_ssid = request.form.get("wifi_ssid", "").strip()
            wifi_password = request.form.get("wifi_password", "").strip()
            tax_rate = parse_float(request.form.get("tax_rate", 0.0))
            receipt_footer = request.form.get("receipt_footer", "").strip()

            if store_name:
                db.execute(
                    "INSERT INTO settings (store_name, brand, currency, timezone, store_address, store_phone, wifi_ssid, wifi_password, tax_rate, receipt_footer)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (store_name, brand, currency, timezone, store_address, store_phone, wifi_ssid, wifi_password, tax_rate, receipt_footer),
                )
                db.commit()
                flash("Settings updated successfully.", "success")
        elif action == "change_password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            user = db.execute(
                "SELECT * FROM users WHERE id = ?", (g.user["id"],)
            ).fetchone()
            if not check_password_hash(user["password_hash"], current):
                flash("Current password is incorrect.", "error")
            elif len(new) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif new != confirm:
                flash("New passwords do not match.", "error")
            else:
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new), g.user["id"]),
                )
                db.commit()
                flash("Password changed successfully.", "success")
        db.close()
        return redirect(url_for("settings"))

    db.close()
    return render_template("settings.html", title="Settings", setting=setting)


# ---------------------------------------------------------------------------
# User management (admin)
# ---------------------------------------------------------------------------
def active_admin_count(db):
    return db.execute(
        "SELECT COUNT(*) AS count FROM users WHERE role = 'Admin' AND active = 1"
    ).fetchone()["count"]


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        target_id = parse_int(request.form.get("user_id"))
        target = db.execute("SELECT * FROM users WHERE id = ?", (target_id,)).fetchone()

        if not target and action != "create":
            flash("User not found.", "error")
        elif action == "create":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "Cashier")
            if role not in ("Admin", "Cashier"):
                role = "Cashier"
            if len(username) < 3 or len(password) < 6:
                flash("Username needs 3+ characters and password 6+.", "error")
            else:
                try:
                    db.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), role),
                    )
                    db.commit()
                    flash(f"User '{username}' created.", "success")
                except sqlite3.IntegrityError:
                    flash(f"Username '{username}' is already taken.", "error")
        elif action == "toggle_active":
            if target["id"] == g.user["id"]:
                flash("You cannot deactivate your own account.", "error")
            elif target["role"] == "Admin" and target["active"] and active_admin_count(db) <= 1:
                flash("At least one active admin is required.", "error")
            else:
                db.execute(
                    "UPDATE users SET active = ? WHERE id = ?",
                    (0 if target["active"] else 1, target["id"]),
                )
                db.commit()
                state = "activated" if target["active"] == 0 else "deactivated"
                flash(f"User '{target['username']}' {state}.", "success")
        elif action == "reset_password":
            new = request.form.get("new_password", "")
            if len(new) < 6:
                flash("Password must be at least 6 characters.", "error")
            else:
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new), target["id"]),
                )
                db.commit()
                flash(f"Password reset for '{target['username']}'.", "success")
        elif action == "delete":
            sold = db.execute(
                "SELECT COUNT(*) AS count FROM orders WHERE cashier_id = ?", (target_id,)
            ).fetchone()["count"]
            if target["id"] == g.user["id"]:
                flash("You cannot delete your own account.", "error")
            elif sold:
                flash(
                    f"'{target['username']}' processed {sold} order(s)."
                    " Deactivate the account instead.",
                    "error",
                )
            elif target["role"] == "Admin" and target["active"] and active_admin_count(db) <= 1:
                flash("At least one active admin is required.", "error")
            else:
                db.execute("DELETE FROM users WHERE id = ?", (target_id,))
                db.commit()
                flash(f"User '{target['username']}' deleted.", "success")
        db.close()
        return redirect(url_for("users"))

    rows = db.execute(
        "SELECT users.*, COUNT(orders.id) AS order_count FROM users"
        " LEFT JOIN orders ON orders.cashier_id = users.id"
        " GROUP BY users.id ORDER BY users.username"
    ).fetchall()
    db.close()
    return render_template("users.html", title="Staff", users=rows)


# ---------------------------------------------------------------------------
# Reports & End of Day Z-Report (admin)
# ---------------------------------------------------------------------------
def report_range():
    """Resolve and validate the requested date range (defaults: last 7 days)."""
    today = datetime.datetime.utcnow()
    default_start = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    start = request.args.get("start", "").strip() or default_start
    end = request.args.get("end", "").strip() or today.strftime("%Y-%m-%d")
    try:
        datetime.datetime.strptime(start, "%Y-%m-%d")
        datetime.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        start, end = default_start, today.strftime("%Y-%m-%d")
    if end < start:
        start, end = end, start
    return start, f"{end} 23:59:59"


@app.route("/reports")
@admin_required
def reports():
    start, end = report_range()
    db = get_db()
    totals = db.execute(
        "SELECT COUNT(*) AS order_count,"
        " COALESCE(SUM(total), 0) AS revenue,"
        " COALESCE(AVG(total), 0) AS avg_order,"
        " COALESCE(SUM(discount), 0) AS discounts,"
        " COALESCE(SUM(tax_amount), 0) AS taxes"
        " FROM orders WHERE status != 'Voided' AND created_at BETWEEN ? AND ?",
        (start, end),
    ).fetchone()
    expense_total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses"
        " WHERE created_at BETWEEN ? AND ?",
        (start, end),
    ).fetchone()["total"]
    payments = db.execute(
        "SELECT payment_method, COUNT(*) AS order_count, SUM(total) AS revenue FROM orders"
        " WHERE status != 'Voided' AND created_at BETWEEN ? AND ?"
        " GROUP BY payment_method ORDER BY revenue DESC",
        (start, end),
    ).fetchall()
    daily = db.execute(
        "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS order_count,"
        " SUM(total) AS revenue FROM orders"
        " WHERE status != 'Voided' AND created_at BETWEEN ? AND ?"
        " GROUP BY day ORDER BY day",
        (start, end),
    ).fetchall()
    top_products = db.execute(
        "SELECT p.name, SUM(oi.quantity) AS qty,"
        " SUM(oi.quantity * oi.unit_price - oi.discount) AS revenue"
        " FROM order_items oi JOIN orders o ON o.id = oi.order_id"
        " JOIN products p ON p.id = oi.product_id"
        " WHERE o.status != 'Voided' AND o.created_at BETWEEN ? AND ?"
        " GROUP BY p.id ORDER BY revenue DESC LIMIT 10",
        (start, end),
    ).fetchall()
    db.close()

    return render_template(
        "reports.html",
        title="Reports & Analytics",
        totals=totals,
        expenses_total=expense_total,
        payments=payments,
        daily=daily,
        top_products=top_products,
        start=start,
        end=end.split(" ")[0],
    )


@app.route("/reports/z-report")
@app.route("/z-report")
@admin_required
def z_report():
    date_str = request.args.get("date", "").strip() or datetime.datetime.utcnow().strftime("%Y-%m-%d")
    db = get_db()
    
    # Orders summary for date
    orders = db.execute(
        "SELECT * FROM orders WHERE created_at LIKE ? AND status != 'Voided'",
        (f"{date_str}%",),
    ).fetchall()
    
    voided_orders = db.execute(
        "SELECT * FROM orders WHERE created_at LIKE ? AND status = 'Voided'",
        (f"{date_str}%",),
    ).fetchall()

    expenses_list = db.execute(
        "SELECT * FROM expenses WHERE created_at LIKE ?",
        (f"{date_str}%",),
    ).fetchall()

    cash_sales = sum(o["total"] for o in orders if o["payment_method"] == "Cash")
    card_sales = sum(o["total"] for o in orders if o["payment_method"] == "Card")
    qr_sales = sum(o["total"] for o in orders if o["payment_method"] == "QR")
    total_sales = sum(o["total"] for o in orders)
    total_discounts = sum(o["discount"] for o in orders)
    total_tax = sum(o["tax_amount"] for o in orders)
    total_expenses = sum(e["amount"] for e in expenses_list)
    net_drawer_cash = cash_sales - total_expenses

    db.close()
    return render_template(
        "z_report.html",
        title=f"Z-Report - {date_str}",
        date=date_str,
        orders_count=len(orders),
        voided_count=len(voided_orders),
        voided_total=sum(o["total"] for o in voided_orders),
        cash_sales=cash_sales,
        card_sales=card_sales,
        qr_sales=qr_sales,
        total_sales=total_sales,
        total_discounts=total_discounts,
        total_tax=total_tax,
        total_expenses=total_expenses,
        net_drawer_cash=net_drawer_cash,
        expenses_list=expenses_list,
    )


@app.route("/reports/export")
@admin_required
def export_report():
    start, end = report_range()
    rows = query_db(
        ORDERS_SELECT + " WHERE orders.created_at BETWEEN ? AND ?"
        " ORDER BY orders.created_at ASC",
        (start, end),
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order Number", "Date", "Customer", "Cashier", "Type", "Table",
                     "Payment Method", "Status", "Discount", "Tax", "Total"])
    for row in rows:
        writer.writerow([
            row["order_number"] or f"#{row['id']}", row["created_at"], row["customer_name"] or "Walk-in",
            row["cashier_name"], row["order_type"], row["table_number"] or "-",
            row["payment_method"], row["status"],
            f"{row['discount']:.2f}", f"{row['tax_amount']:.2f}", f"{row['total']:.2f}",
        ])
    filename = f"sales_{start}_{end.split(' ')[0]}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Real-Time REST APIs for KDS, Live Tracking, Chart Data & POS Quick Customer
# ---------------------------------------------------------------------------
@app.route("/api/orders/<string:order_identifier>/status")
def api_order_status(order_identifier):
    order = query_db(
        "SELECT o.id, o.order_number, o.order_status, o.status, o.total, o.created_at, o.customer_name, "
        "t.table_number "
        "FROM orders o LEFT JOIN cafe_tables t ON t.id = o.table_id "
        "WHERE o.order_number = ? OR CAST(o.id AS TEXT) = ?",
        (order_identifier, order_identifier),
        one=True,
    )
    if not order:
        return jsonify({"found": False, "error": "Order not found"}), 404
    
    return jsonify({
        "found": True,
        "id": order["id"],
        "order_number": order["order_number"] or f"CAF-{order['id']}",
        "order_status": order["order_status"] or order["status"],
        "status": order["status"],
        "table_number": order["table_number"],
        "customer_name": order["customer_name"],
        "created_at": order["created_at"],
    })


@app.route("/api/kitchen/orders")
@login_required
def api_kitchen_orders():
    db = get_db()
    rows = db.execute(
        "SELECT orders.id, orders.order_number, orders.order_status, orders.order_type, "
        "orders.created_at, orders.notes, orders.customer_name, cafe_tables.table_number "
        "FROM orders LEFT JOIN cafe_tables ON orders.table_id = cafe_tables.id "
        "WHERE orders.status != 'Voided' AND orders.order_status IN ('Pending', 'Preparing', 'Ready') "
        "ORDER BY orders.created_at ASC"
    ).fetchall()

    orders_data = []
    for r in rows:
        items = db.execute(
            "SELECT oi.quantity, oi.options, p.name AS product_name "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?",
            (r["id"],),
        ).fetchall()
        orders_data.append({
            "id": r["id"],
            "order_number": r["order_number"] or f"CAF-{r['id']}",
            "order_status": r["order_status"],
            "order_type": r["order_type"],
            "table_number": r["table_number"],
            "customer_name": r["customer_name"] or "Walk-in",
            "created_at": r["created_at"],
            "notes": r["notes"] or "",
            "items": [{"name": i["product_name"], "qty": i["quantity"], "options": i["options"]} for i in items],
        })
    db.close()
    return jsonify({"orders": orders_data, "count": len(orders_data)})


@app.route("/api/kitchen/update-status", methods=["POST"])
@login_required
def api_kitchen_update_status():
    data = request.get_json(silent=True) or request.form
    order_id = parse_int(data.get("order_id"))
    status = str(data.get("status", "")).strip()
    if not order_id or status not in ("Pending", "Preparing", "Ready", "Completed", "Cancelled"):
        return jsonify({"success": False, "error": "Invalid order ID or status"}), 400
    
    db = get_db()
    db.execute("UPDATE orders SET order_status = ?, status = ? WHERE id = ?", (status, status, order_id))
    db.commit()
    db.close()
    return jsonify({"success": True, "order_id": order_id, "status": status})


@app.route("/api/customers/quick-create", methods=["POST"])
@login_required
def api_quick_create_customer():
    data = request.get_json(silent=True) or request.form
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    email = str(data.get("email", "")).strip()
    notes = str(data.get("notes", "")).strip()

    if not name:
        return jsonify({"success": False, "error": "Customer name is required"}), 400

    db = get_db()
    cursor = db.execute(
        "INSERT INTO customers (name, phone, email, notes, points) VALUES (?, ?, ?, ?, 0)",
        (name, phone, email, notes),
    )
    cust_id = cursor.lastrowid
    db.commit()
    db.close()
    return jsonify({"success": True, "customer": {"id": cust_id, "name": name, "phone": phone, "points": 0}})


@app.route("/api/customers/<int:customer_id>")
@login_required
def api_get_customer(customer_id):
    db = get_db()
    cust = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not cust:
        db.close()
        return jsonify({"found": False}), 404
    spent = db.execute(
        "SELECT COALESCE(SUM(total), 0) AS total FROM orders WHERE customer_id = ? AND status != 'Voided'",
        (customer_id,),
    ).fetchone()["total"]
    db.close()
    return jsonify({
        "found": True,
        "id": cust["id"],
        "name": cust["name"],
        "phone": cust["phone"] or "",
        "points": cust["points"] or 0,
        "spent": float(spent),
        "tier": get_customer_tier(spent),
    })


@app.route("/api/reports/chart-data")
@login_required
def api_chart_data():
    db = get_db()
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Hourly curve for today
    hourly_raw = db.execute(
        "SELECT substr(created_at, 12, 2) AS hour, COUNT(*) AS count, SUM(total) AS revenue "
        "FROM orders WHERE created_at LIKE ? AND status != 'Voided' "
        "GROUP BY hour ORDER BY hour ASC",
        (f"{today}%",),
    ).fetchall()
    hourly_dict = {f"{int(r['hour']):02d}:00": {"count": r["count"], "revenue": round(r["revenue"], 2)} for r in hourly_raw}
    hours = [f"{h:02d}:00" for h in range(7, 23)]
    hourly_counts = [hourly_dict.get(h, {}).get("count", 0) for h in hours]
    hourly_revenues = [hourly_dict.get(h, {}).get("revenue", 0.0) for h in hours]

    # 2. 7-Day sales vs expenses
    seven_days = [(datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    daily_sales_raw = db.execute(
        "SELECT substr(created_at, 1, 10) AS day, SUM(total) AS revenue FROM orders "
        "WHERE created_at >= ? AND status != 'Voided' GROUP BY day",
        (seven_days[0],),
    ).fetchall()
    daily_sales_map = {r["day"]: float(r["revenue"]) for r in daily_sales_raw}

    daily_exp_raw = db.execute(
        "SELECT substr(created_at, 1, 10) AS day, SUM(amount) AS expense FROM expenses "
        "WHERE created_at >= ? GROUP BY day",
        (seven_days[0],),
    ).fetchall()
    daily_exp_map = {r["day"]: float(r["expense"]) for r in daily_exp_raw}

    trend_sales = [daily_sales_map.get(d, 0.0) for d in seven_days]
    trend_exp = [daily_exp_map.get(d, 0.0) for d in seven_days]

    # 3. Payment methods
    payment_raw = db.execute(
        "SELECT payment_method, SUM(total) AS revenue FROM orders WHERE status != 'Voided' GROUP BY payment_method"
    ).fetchall()
    payment_labels = [r["payment_method"] for r in payment_raw]
    payment_values = [round(float(r["revenue"]), 2) for r in payment_raw]

    db.close()
    return jsonify({
        "hourly": {"labels": hours, "counts": hourly_counts, "revenues": hourly_revenues},
        "trend": {"labels": [d[5:] for d in seven_days], "sales": trend_sales, "expenses": trend_exp},
        "payments": {"labels": payment_labels, "values": payment_values},
    })


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", title="404", code=404,
                           message="The page you are looking for could not be found."), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", title="403", code=403,
                           message="You do not have permission to access this page."), 403


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", title="400", code=400,
                           message=getattr(error, "description", "Bad request.")), 400


# Initialize database on import (needed for gunicorn/production)
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
