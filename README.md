# Cafe Shop Management System

A complete, real-world cafe management and point-of-sale web app built with **Flask + SQLite**.
Server-rendered Jinja templates with a warm coffee-house UI - no build step required.

## Features

### Accounts & security
- Admin and Cashier roles with role-based access control
- Session-based login, CSRF protection on every form
- User management (create staff, activate/deactivate, reset passwords)
- Self-service password change for every user

### Point of sale
- Category-filtered product grid with live stock levels
- Product customization modal (options from tags + kitchen note + quantity)
- Cart with quantity limits based on stock, discounts, paid amount and change due
- Server-side price authority (client prices are never trusted) and stock validation
- Printable receipt with item options, discount, paid amount and change
- Orders can be voided by an admin (stock is automatically restored)

### Management
- Dashboard: today/week/month revenue, expenses, top sellers, low-stock alerts
- Products: add/edit/delete products and categories (with safety guards)
- Inventory: adjust stock levels, low/out-of-stock highlighting, inventory value
- Customers: full CRUD plus order count and lifetime spend
- Expenses: categorised expense tracking with delete
- Reports: date-range sales report (daily sales, payment methods, top products,
  net profit) with CSV export

## Run Locally

1. Create a Python environment:

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
venv\Scripts\activate          # PowerShell / CMD
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

4. Open http://127.0.0.1:5000

On first run `cafe.db` is created automatically with demo users, categories and
a sample menu. On later runs the schema is upgraded in place if needed.

## Default Users

- Admin: `admin` / `admin123`
- Cashier: `cashier` / `cashier123`

> Change these passwords after first login (Settings -> Change My Password).

## Roles at a glance

| Page       | Cashier | Admin |
| ---------- | :-----: | :---: |
| Dashboard  |   yes   |  yes  |
| POS        |   yes   |  yes  |
| Orders     |   yes   |  yes  |
| Receipts   |   yes   |  yes  |
| Customers  |   yes   |  yes  |
| Settings*  |   yes   |  yes  |
| Products   |    -    |  yes  |
| Inventory  |    -    |  yes  |
| Expenses   |    -    |  yes  |
| Reports    |    -    |  yes  |
| Users      |    -    |  yes  |
| Void order |    -    |  yes  |

\* Everyone can change their own password; only admins can edit store settings.

## Configuration

- `SECRET_KEY` environment variable overrides the default dev secret:
  `set SECRET_KEY=something-random` before running.
- Low-stock threshold defaults to 5 units (`LOW_STOCK_THRESHOLD` in `app.py`).

## Project layout

```
app.py            Flask application (routes, auth, reports, CSV export)
templates/        Jinja pages (dashboard, pos, inventory, reports, ...)
static/css        Stylesheet
static/js         POS cart + customization modal logic
cafe.db           SQLite database (auto-created)
archive/          Archived Next.js prototype fragments (not part of the app)
```
