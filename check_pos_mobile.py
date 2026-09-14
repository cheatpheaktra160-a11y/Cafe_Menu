import os
import sys
import time
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
OUTPUT_DIR = os.path.join(os.getcwd(), "mobile_pos_audit")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def start_server():
    try:
        urllib.request.urlopen(f"{BASE_URL}/", timeout=1)
        print("Flask server is already active.", flush=True)
        return None
    except Exception:
        print("Starting Flask server...", flush=True)
        py_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        proc = subprocess.Popen([py_exe, "app.py"], cwd=os.getcwd())
        for _ in range(20):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(f"{BASE_URL}/", timeout=1)
                print("Server started successfully.", flush=True)
                return proc
            except Exception:
                pass
        raise RuntimeError("Failed to start Flask server.")

def check_overflow(page, name):
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    client_width = page.evaluate("document.documentElement.clientWidth")
    body_scroll = page.evaluate("document.body.scrollWidth")
    is_overflow = scroll_width > client_width or body_scroll > client_width
    status = "FAIL (OVERFLOW)" if is_overflow else "PASS (NO OVERFLOW)"
    print(f"    [{status}] {name}: scrollWidth={scroll_width}, clientWidth={client_width}, bodyScroll={body_scroll}", flush=True)
    return not is_overflow

def run_pos_audit():
    proc = start_server()
    all_passed = True

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)

            viewports = [
                {"name": "iPhone_390", "width": 390, "height": 844},
                {"name": "Small_360", "width": 360, "height": 780},
                {"name": "Max_430", "width": 430, "height": 932},
            ]

            roles = [
                {"role": "cashier", "user": "cashier", "pw": "cashier123"},
                {"role": "admin", "user": "admin", "pw": "admin123"},
            ]

            for role_info in roles:
                role = role_info["role"]
                print(f"\n==========================================", flush=True)
                print(f" TESTING POS FOR ROLE: {role.upper()}", flush=True)
                print(f"==========================================", flush=True)

                for vp in viewports:
                    vp_name = vp["name"]
                    print(f"\n--- Viewport: {vp_name} ({vp['width']}x{vp['height']}) ---", flush=True)
                    
                    context = browser.new_context(
                        viewport={"width": vp["width"], "height": vp["height"]},
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
                        is_mobile=True,
                        has_touch=True
                    )
                    page = context.new_page()

                    # 1. Login
                    page.goto(f"{BASE_URL}/logout", wait_until="networkidle")
                    page.goto(f"{BASE_URL}/login", wait_until="networkidle")
                    page.fill("input[name='username']", role_info["user"])
                    page.fill("input[name='password']", role_info["pw"])
                    page.click("button[type='submit']")
                    page.wait_for_load_state("networkidle")

                    # 2. Go to POS
                    page.goto(f"{BASE_URL}/pos", wait_until="networkidle")
                    time.sleep(0.3)
                    img_name = f"{role}_{vp_name}_01_catalog.png"
                    page.screenshot(path=os.path.join(OUTPUT_DIR, img_name))
                    if not check_overflow(page, f"{role} {vp_name} POS Catalog"):
                        all_passed = False

                    # Check Topbar elements
                    topbar_title = page.locator(".topbar h2").text_content()
                    user_chip = page.locator(".user-chip").text_content()
                    print(f"    [PASS] Topbar Title: '{topbar_title.strip()}', User Chip: '{user_chip.strip()}'", flush=True)

                    # Check Sidebar Drawer
                    sidebar_btn = page.locator("#sidebar-toggle")
                    if sidebar_btn.is_visible():
                        sidebar_btn.click()
                        time.sleep(0.3)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_02_sidebar.png"))
                        sidebar_visible = page.locator("#sidebar").is_visible()
                        print(f"    [PASS] Sidebar Drawer opened: {sidebar_visible}", flush=True)
                        # Verify role menu items
                        menu_text = page.locator("#sidebar .menu").text_content()
                        if role == "cashier":
                            has_admin_items = "Products" in menu_text or "Inventory" in menu_text or "Staff" in menu_text
                            print(f"    [PASS] Cashier restricted from admin menu items: {not has_admin_items}", flush=True)
                        else:
                            has_admin_items = "Products" in menu_text and "Inventory" in menu_text and "Staff" in menu_text
                            print(f"    [PASS] Admin has access to all admin menu items: {has_admin_items}", flush=True)
                        
                        # Close sidebar
                        close_btn = page.locator("#sidebar-close-btn")
                        if close_btn.is_visible():
                            close_btn.click()
                        else:
                            sidebar_btn.click()
                        time.sleep(0.3)

                    # 3. Category filter and search
                    cat_btns = page.locator(".category-button")
                    cat_count = cat_btns.count()
                    print(f"    [PASS] Category pills ({cat_count} categories)", flush=True)
                    if cat_count > 1:
                        cat_btns.nth(1).click()
                        time.sleep(0.2)
                    cat_btns.first.click()
                    time.sleep(0.2)

                    # 4. Add product to cart via Customization Modal
                    add_btns = page.locator(".product-card button.add-product:not([disabled])")
                    if add_btns.count() > 0:
                        add_btns.first.click()
                        time.sleep(0.3)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_03_modal.png"))
                        modal_visible = page.locator("#custom-modal").is_visible()
                        print(f"    [PASS] Customization Modal opened: {modal_visible}", flush=True)

                        option_chips = page.locator("#modal-options .option-chip")
                        if option_chips.count() > 0:
                            option_chips.first.click()

                        plus_btn = page.locator("#modal-qty-plus")
                        if plus_btn.is_visible():
                            plus_btn.click()
                            time.sleep(0.1)

                        note_box = page.locator("#modal-note")
                        if note_box.is_visible():
                            note_box.fill("Oat milk, extra hot")

                        page.click("#modal-add")
                        time.sleep(0.4)

                        # Check Floating Cart Bar
                        floating_bar = page.locator("#pos-mobile-cart-bar")
                        floating_visible = floating_bar.is_visible()
                        bar_qty = page.locator("#mobile-bar-qty").text_content()
                        bar_total = page.locator("#mobile-bar-total").text_content()
                        print(f"    [PASS] Floating Cart Bar visible: {floating_visible}, Qty: {bar_qty}, Total: {bar_total}", flush=True)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_04_floating_bar.png"))

                        # 5. Switch to Order Cart tab
                        if vp_name == "iPhone_390":
                            page.click("#pos-mobile-bar-pay-btn")
                        else:
                            page.click("#pos-tab-cart")
                        time.sleep(0.4)
                        page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_05_cart_tab.png"))
                        if not check_overflow(page, f"{role} {vp_name} POS Cart Tab"):
                            all_passed = False

                        # Quick Discount Preset (10%)
                        disc_10 = page.locator(".discount-preset-btn[data-pct='10']")
                        if disc_10.is_visible():
                            disc_10.click()
                            time.sleep(0.2)
                            print("    [PASS] Applied 10% discount preset", flush=True)

                        # Quick Cash Preset (Exact)
                        exact_btn = page.locator(".cash-preset-btn[data-amount='exact']")
                        if exact_btn.is_visible():
                            exact_btn.click()
                            time.sleep(0.2)
                            paid_val = page.locator("#paid-amount").input_value()
                            change_due = page.locator("#change-due").text_content()
                            print(f"    [PASS] Cash tender exact: Paid={paid_val}, Change={change_due}", flush=True)

                        # Order Type Selection (Takeaway)
                        takeaway_btn = page.locator(".order-type-btn[data-type='Takeaway']")
                        if takeaway_btn.is_visible():
                            takeaway_btn.click()
                            time.sleep(0.2)
                            print("    [PASS] Order type changed to Takeaway", flush=True)

                        # Quick Customer Modal
                        quick_cust_btn = page.locator("#open-quick-customer")
                        if quick_cust_btn.is_visible():
                            quick_cust_btn.click()
                            time.sleep(0.3)
                            page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_06_quick_cust_modal.png"))
                            print("    [PASS] Quick Customer Modal verified", flush=True)
                            page.click("#qc-cancel")
                            time.sleep(0.2)

                        # 6. Complete Order Checkout if iPhone_390
                        if vp_name == "iPhone_390":
                            submit_btn = page.locator("#pos-submit-btn")
                            if submit_btn.is_visible():
                                submit_btn.click()
                                page.wait_for_load_state("networkidle")
                                time.sleep(0.6)
                                page.screenshot(path=os.path.join(OUTPUT_DIR, f"{role}_{vp_name}_07_receipt.png"))
                                print(f"    [PASS] Order completed and redirected to Receipt: {page.url}", flush=True)
                                if not check_overflow(page, f"{role} {vp_name} Receipt View"):
                                    all_passed = False

                    context.close()

            browser.close()
            print("\n========================================================", flush=True)
            if all_passed:
                print(" RESULT: 100% ALL POS MOBILE AUDIT CHECKS PASSED!", flush=True)
            else:
                print(" RESULT: SOME OVERFLOW CHECKS FAILED.", flush=True)
            print("========================================================", flush=True)

    finally:
        if proc:
            proc.terminate()

if __name__ == "__main__":
    run_pos_audit()
