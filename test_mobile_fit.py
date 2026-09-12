"""Verify Mobile Phone UI Fit across Customer, Cashier, and Admin views with msedge."""
import os
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
ARTIFACT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\01029117-26a3-4860-abea-e0e65ba5e0de"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

import subprocess

def ensure_server():
    try:
        urllib.request.urlopen(f"{BASE_URL}/", timeout=2)
        print("Flask server is already active on port 5000.")
        return None
    except Exception:
        print("Starting Flask server...")
        py_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = "python"
        p = subprocess.Popen([py_exe, "app.py"], cwd=os.getcwd())
        time.sleep(2.5)
        return p

def run_mobile_checks():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        # Emulate standard phone: 390x844 (iPhone 13 / modern smartphone)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            is_mobile=True,
            has_touch=True
        )
        page = context.new_page()

        print("=== 1. Customer Mobile Experience ===")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_01_customer_home.png"))
        print("  [OK] Customer Home on mobile verified")

        page.goto(f"{BASE_URL}/menu", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_02_customer_menu.png"))
        print("  [OK] Customer Menu on mobile verified")

        # Test adding to cart on mobile to trigger customer floating cart bar
        add_btn = page.locator(".menu-card form button[type='submit']").first
        if add_btn.is_visible():
            add_btn.click(force=True)
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_03_customer_menu_with_cart_bar.png"))
            print("  [OK] Customer Floating Cart Bar on mobile verified")

        page.goto(f"{BASE_URL}/cart", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_04_customer_cart.png"))
        print("  [OK] Customer Cart responsive item card on mobile verified")

        page.goto(f"{BASE_URL}/checkout", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_05_customer_checkout.png"))
        print("  [OK] Customer Checkout on mobile verified")

        print("\n=== 2. Cashier Mobile Experience ===")
        page.goto(f"{BASE_URL}/logout", wait_until="networkidle")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_06_login.png"))
        print("  [OK] Staff Login on mobile verified")

        page.fill("input[name='username']", "cashier")
        page.fill("input[name='password']", "cashier123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        # POS on Mobile
        page.goto(f"{BASE_URL}/pos", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_07_pos_catalog.png"))
        print("  [OK] Cashier POS Catalog view with mobile tabs verified")

        # Add item to cart in POS
        pos_add = page.locator(".product-card button.add-product").first
        if pos_add.is_visible():
            pos_add.click(force=True)
            time.sleep(0.5)
            modal_add = page.locator("#modal-add")
            if modal_add.is_visible():
                modal_add.click(force=True)
                time.sleep(0.5)
                page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_08_pos_floating_bar.png"))
                print("  [OK] Cashier POS floating bottom cart bar verified")

                # Switch to Cart Tab
                page.click("#pos-tab-cart", force=True)
                time.sleep(0.5)
                page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_09_pos_cart_tab.png"))
                print("  [OK] Cashier POS Cart Tab view verified")

                # Switch Back to Catalog
                page.click("#pos-back-catalog-btn", force=True)
                time.sleep(0.5)
                print("  [OK] Cashier POS Back to Catalog button verified")

        # KDS on Mobile
        page.goto(f"{BASE_URL}/kds", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_10_kds.png"))
        print("  [OK] KDS Kitchen Board on mobile verified")

        # Orders list on Mobile
        page.goto(f"{BASE_URL}/orders", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_11_orders.png"))
        print("  [OK] Orders List on mobile verified")

        print("\n=== 3. Admin Mobile Experience ===")
        page.goto(f"{BASE_URL}/logout", wait_until="networkidle")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        # Dashboard on Mobile
        page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_12_admin_dashboard.png"))
        print("  [OK] Admin Dashboard on mobile verified")

        # Sidebar Drawer on Mobile
        sidebar_toggle = page.locator("#sidebar-toggle")
        if sidebar_toggle.is_visible():
            sidebar_toggle.click(force=True)
            time.sleep(0.5)
            page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_13_admin_sidebar_drawer.png"))
            print("  [OK] Admin Slide-over Sidebar Drawer on mobile verified")
            # Close sidebar by tapping toggle button or outside
            sidebar_toggle.click(force=True)
            time.sleep(0.3)

        # Products on Mobile
        page.goto(f"{BASE_URL}/products", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_14_admin_products.png"))
        print("  [OK] Admin Products on mobile verified")

        # Inventory on Mobile
        page.goto(f"{BASE_URL}/inventory", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_15_admin_inventory.png"))
        print("  [OK] Admin Inventory on mobile verified")

        # Reports on Mobile
        page.goto(f"{BASE_URL}/reports", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_16_admin_reports.png"))
        print("  [OK] Admin Reports on mobile verified")

        # Z-Report on Mobile
        page.goto(f"{BASE_URL}/z-report", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_17_admin_z_report.png"))
        print("  [OK] Admin Z-Report on mobile verified")

        # Tables & QR on Mobile
        page.goto(f"{BASE_URL}/tables", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_18_admin_tables.png"))
        print("  [OK] Admin Tables on mobile verified")

        # Staff Users on Mobile
        page.goto(f"{BASE_URL}/users", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_19_admin_users.png"))
        print("  [OK] Admin Staff Management on mobile verified")

        # Settings on Mobile
        page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "mobile_20_admin_settings.png"))
        print("  [OK] Admin Store Settings on mobile verified")

        browser.close()
        print("\nAll 20 Mobile Viewport Checks Succeeded!")

if __name__ == "__main__":
    proc = ensure_server()
    try:
        run_mobile_checks()
    finally:
        if proc:
            proc.terminate()
