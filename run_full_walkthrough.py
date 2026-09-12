import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\8c10c3f7-4071-4414-b534-d9f8a605d93e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []

def log_step(step_no, name, status, details=None):
    entry = {
        "step": step_no,
        "name": name,
        "status": status,
        "details": details or {}
    }
    results.append(entry)
    print(f"[{'PASS' if status == 'SUCCESS' else 'FAIL'}] Step {step_no}: {name}")
    if details:
        for k, v in details.items():
            print(f"   - {k}: {v}")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    # Step 1: Open Public Home
    print("\n--- Step 1: Public Home Page ---")
    res = page.goto("http://127.0.0.1:5000", wait_until="networkidle")
    home_shot = os.path.join(SCREENSHOT_DIR, "01_public_home.png")
    page.screenshot(path=home_shot, full_page=False)
    log_step(1, "Public Home Page Load", "SUCCESS" if res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "status_code": res.status,
        "screenshot": home_shot
    })

    # Step 2: Locate and Click 'Staff Login'
    print("\n--- Step 2: Click Staff Login Link ---")
    login_btn = page.locator("a:has-text('Staff Login')")
    has_btn = login_btn.count() > 0
    if has_btn:
        login_btn.first.click()
        page.wait_for_load_state("networkidle")
        login_page_shot = os.path.join(SCREENSHOT_DIR, "02_login_page.png")
        page.screenshot(path=login_page_shot, full_page=False)
        log_step(2, "Click 'Staff Login' Link", "SUCCESS", {
            "url": page.url,
            "title": page.title(),
            "screenshot": login_page_shot
        })
    else:
        log_step(2, "Click 'Staff Login' Link", "FAILED", {"error": "Staff Login link not found"})

    # Step 3: Fill credentials and submit login form
    print("\n--- Step 3: Fill Credentials & Submit Login ---")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    
    cred_filled_shot = os.path.join(SCREENSHOT_DIR, "03_login_filled.png")
    page.screenshot(path=cred_filled_shot, full_page=False)
    
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    time.sleep(1) # Allow any animations or redirects to settle
    
    log_step(3, "Submit Login Form (admin / admin123)", "SUCCESS" if "login" not in page.url else "FAILED", {
        "current_url": page.url,
        "page_title": page.title()
    })

    # Step 4: Dashboard page load & screenshot
    print("\n--- Step 4: Dashboard Page ---")
    if not page.url.endswith("/dashboard"):
        page.goto("http://127.0.0.1:5000/dashboard", wait_until="networkidle")
    time.sleep(1)
    dash_shot = os.path.join(SCREENSHOT_DIR, "04_dashboard.png")
    page.screenshot(path=dash_shot, full_page=False)
    
    # Check stats cards
    stat_cards = page.locator(".stat-card, .metric-card, .card").all_text_contents()
    log_step(4, "Dashboard Page Load & Screenshot", "SUCCESS", {
        "url": page.url,
        "title": page.title(),
        "cards_found": len(stat_cards),
        "screenshot": dash_shot
    })

    # Step 5: POS page load & screenshot
    print("\n--- Step 5: Point of Sale (POS) Page ---")
    pos_res = page.goto("http://127.0.0.1:5000/pos", wait_until="networkidle")
    time.sleep(1)
    pos_shot = os.path.join(SCREENSHOT_DIR, "05_pos.png")
    page.screenshot(path=pos_shot, full_page=False)
    
    products_count = page.locator(".pos-item, .product-card, .pos-product-card").count()
    categories_count = page.locator(".pos-category-btn, .category-tab, .filter-chip").count()
    log_step(5, "Point of Sale (POS) Page Load & Screenshot", "SUCCESS" if pos_res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "products_visible": products_count,
        "categories_visible": categories_count,
        "screenshot": pos_shot
    })

    # Step 6: Kitchen (KDS) page load & screenshot
    print("\n--- Step 6: Kitchen Display System (KDS) Page ---")
    kds_res = page.goto("http://127.0.0.1:5000/kds", wait_until="networkidle")
    time.sleep(1)
    kds_shot = os.path.join(SCREENSHOT_DIR, "06_kds.png")
    page.screenshot(path=kds_shot, full_page=False)
    
    kds_cards = page.locator(".kds-card, .order-ticket, .kds-order").count()
    log_step(6, "Kitchen (KDS) Page Load & Screenshot", "SUCCESS" if kds_res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "active_tickets": kds_cards,
        "screenshot": kds_shot
    })

    # Step 7: Reports & Analytics page load & screenshot
    print("\n--- Step 7: Reports & Analytics Page ---")
    rep_res = page.goto("http://127.0.0.1:5000/reports", wait_until="networkidle")
    time.sleep(1)
    rep_shot = os.path.join(SCREENSHOT_DIR, "07_reports.png")
    page.screenshot(path=rep_shot, full_page=False)
    
    charts_count = page.locator("canvas, .chart-box, .chart-container").count()
    log_step(7, "Reports & Analytics Page Load & Screenshot", "SUCCESS" if rep_res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "charts_found": charts_count,
        "screenshot": rep_shot
    })

    # Step 8: Tables & QR page load & screenshot
    print("\n--- Step 8: Tables & QR Page ---")
    tab_res = page.goto("http://127.0.0.1:5000/tables", wait_until="networkidle")
    time.sleep(1)
    tab_shot = os.path.join(SCREENSHOT_DIR, "08_tables.png")
    page.screenshot(path=tab_shot, full_page=False)
    
    tables_count = page.locator(".table-card, .qr-card, tr[data-table-id], .table-grid > *").count()
    log_step(8, "Tables & QR Page Load & Screenshot", "SUCCESS" if tab_res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "tables_count": tables_count,
        "screenshot": tab_shot
    })

    # Step 9: Store Settings page load & screenshot
    print("\n--- Step 9: Store Settings Page ---")
    set_res = page.goto("http://127.0.0.1:5000/settings", wait_until="networkidle")
    time.sleep(1)
    set_shot = os.path.join(SCREENSHOT_DIR, "09_settings.png")
    page.screenshot(path=set_shot, full_page=False)
    
    form_inputs = page.locator("input, select, textarea").count()
    log_step(9, "Store Settings Page Load & Screenshot", "SUCCESS" if set_res.status == 200 else "FAILED", {
        "url": page.url,
        "title": page.title(),
        "setting_fields_count": form_inputs,
        "screenshot": set_shot
    })

    browser.close()

# Step 10: Generate JSON report
report_path = os.path.join(SCREENSHOT_DIR, "walkthrough_results.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\n--- Step 10: Walkthrough Complete ---")
print(f"Results written to {report_path}")
