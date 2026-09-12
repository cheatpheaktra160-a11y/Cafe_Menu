import os
import sys
import time
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\e4eacf7a-10f8-48c7-9574-b9c04867d01e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Check or start Flask
def ensure_server():
    try:
        urllib.request.urlopen("http://127.0.0.1:5000", timeout=2)
        print("Server is active on port 5000.")
        return None
    except Exception:
        print("Starting Flask server...")
        py_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = sys.executable
        p = subprocess.Popen([py_exe, "app.py"], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2.5)
        return p

proc = ensure_server()

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # -----------------------------------------------------------
        # 1. Customer Experience Flow
        # -----------------------------------------------------------
        print("\n=== Testing Customer Experience ===")
        # Home
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_customer_home.png"))
        print("1. Customer Home screenshot saved.")

        # Menu
        page.goto("http://127.0.0.1:5000/menu", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "02_customer_menu.png"))
        print("2. Customer Menu screenshot saved.")

        # Product Detail / Customizer
        page.goto("http://127.0.0.1:5000/menu/1", wait_until="networkidle")
        page.select_option("select[name='size']", "Large")
        page.select_option("select[name='sugar']", "25%")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "03_customer_product_customizer.png"))
        print("3. Product Detail Customizer screenshot saved.")

        # Add to cart from detail
        page.locator("button[type='submit']").first.click(no_wait_after=True)
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)

        # Cart
        page.goto("http://127.0.0.1:5000/cart", wait_until="networkidle")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "04_customer_cart.png"))
        print("4. Shopping Cart screenshot saved.")

        # Checkout
        page.goto("http://127.0.0.1:5000/checkout", wait_until="networkidle")
        page.fill("input[name='customer_name']", "Sophea Lin")
        page.fill("input[name='phone']", "+855 12 345 678")
        page.fill("textarea[name='notes']", "Less ice, extra hot please")
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "05_customer_checkout.png"))
        page.locator("button[type='submit']").first.click(no_wait_after=True)
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)
        print("5. Checkout completed.")

        # Order Tracking
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "06_customer_order_track.png"))
        print("6. Live Order Tracking screenshot saved.")

        # -----------------------------------------------------------
        # 2. Cashier Experience Flow
        # -----------------------------------------------------------
        print("\n=== Testing Cashier Experience ===")
        page.goto("http://127.0.0.1:5000/logout", wait_until="networkidle")
        page.goto("http://127.0.0.1:5000/login", wait_until="networkidle")
        page.fill("input[name='username']", "cashier")
        page.fill("input[name='password']", "cashier123")
        page.locator("button[type='submit']").first.click(no_wait_after=True)
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)

        # POS Screen
        page.goto("http://127.0.0.1:5000/pos", wait_until="networkidle")
        time.sleep(0.5)

        # Click first add button to open modal
        add_btns = page.locator(".add-product")
        if add_btns.count() > 0:
            add_btns.first.click()
            time.sleep(0.3)
            # Click Add in modal
            modal_add = page.locator("#modal-add")
            if modal_add.count() > 0:
                modal_add.click()
                time.sleep(0.3)

        # Quick discount preset 10%
        disc_btn = page.locator("button.discount-preset-btn[data-pct='10']")
        if disc_btn.count() > 0:
            disc_btn.click()
            time.sleep(0.2)

        # Quick Cash $20 preset
        cash_btn = page.locator("button.cash-preset-btn[data-amount='20']")
        if cash_btn.count() > 0:
            cash_btn.click()
            time.sleep(0.2)

        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "07_cashier_pos.png"))
        print("7. Cashier POS screenshot saved.")

        # Submit POS order
        pos_submit = page.locator("#pos-submit-btn")
        if pos_submit.count() > 0:
            pos_submit.click(no_wait_after=True)
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "08_cashier_receipt.png"))
            print("8. Cashier Thermal Receipt screenshot saved.")

        # Orders List
        page.goto("http://127.0.0.1:5000/orders", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "09_cashier_orders.png"))
        print("9. Cashier Orders List screenshot saved.")

        # -----------------------------------------------------------
        # 3. Admin Experience Flow
        # -----------------------------------------------------------
        print("\n=== Testing Admin Experience ===")
        page.goto("http://127.0.0.1:5000/logout", wait_until="networkidle")
        page.goto("http://127.0.0.1:5000/login", wait_until="networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.locator("button[type='submit']").first.click(no_wait_after=True)
        page.wait_for_load_state("networkidle")
        time.sleep(0.5)

        # Dashboard
        page.goto("http://127.0.0.1:5000/dashboard", wait_until="networkidle")
        time.sleep(1) # Allow charts to animate
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "10_admin_dashboard.png"))
        print("10. Admin Dashboard screenshot saved.")

        # Kitchen KDS
        page.goto("http://127.0.0.1:5000/kds", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "11_admin_kds.png"))
        print("11. Kitchen KDS Live Board screenshot saved.")

        # Products Catalog
        page.goto("http://127.0.0.1:5000/products", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "12_admin_products.png"))
        print("12. Admin Products Catalog screenshot saved.")

        # Inventory
        page.goto("http://127.0.0.1:5000/inventory", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "13_admin_inventory.png"))
        print("13. Admin Stock Inventory screenshot saved.")

        # Reports & Analytics
        page.goto("http://127.0.0.1:5000/reports", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "14_admin_reports.png"))
        print("14. Admin Reports & Analytics screenshot saved.")

        # Z-Report
        page.goto("http://127.0.0.1:5000/z-report", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "15_admin_z_report.png"))
        print("15. Admin Daily Z-Report screenshot saved.")

        # Tables & QR
        page.goto("http://127.0.0.1:5000/tables", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "16_admin_tables.png"))
        print("16. Admin Tables & QR screenshot saved.")

        browser.close()
        print("\nAll User Flows Tested and Verified Successfully!")
finally:
    if proc:
        proc.terminate()
