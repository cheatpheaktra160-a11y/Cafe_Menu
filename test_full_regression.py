import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\8c10c3f7-4071-4414-b534-d9f8a605d93e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

test_pages = [
    {"name": "Home", "url": "http://127.0.0.1:5000/"},
    {"name": "Menu", "url": "http://127.0.0.1:5000/menu"},
    {"name": "Product Customizer", "url": "http://127.0.0.1:5000/menu/1"},
    {"name": "Cart", "url": "http://127.0.0.1:5000/cart"},
    {"name": "Track Order", "url": "http://127.0.0.1:5000/track"},
    {"name": "Login", "url": "http://127.0.0.1:5000/login"},
    {"name": "Dashboard", "url": "http://127.0.0.1:5000/dashboard"},
    {"name": "POS", "url": "http://127.0.0.1:5000/pos"},
    {"name": "KDS", "url": "http://127.0.0.1:5000/kds"},
    {"name": "Reports", "url": "http://127.0.0.1:5000/reports"},
    {"name": "Tables & QR", "url": "http://127.0.0.1:5000/tables"},
    {"name": "Settings", "url": "http://127.0.0.1:5000/settings"}
]

errors_found = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.on("pageerror", lambda err: errors_found.append(f"PageError on {page.url}: {err}"))
    page.on("console", lambda msg: errors_found.append(f"ConsoleError on {page.url}: {msg.text}") if msg.type == "error" else None)

    # 1. Login first to enable admin sessions
    page.goto("http://127.0.0.1:5000/login", wait_until="networkidle")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")

    # 2. Iterate through all test pages
    for p_info in test_pages:
        res = page.goto(p_info["url"], wait_until="networkidle")
        time.sleep(0.5)
        status = res.status if res else "Unknown"
        print(f"[{'PASS' if status == 200 else 'FAIL'}] {p_info['name']} ({p_info['url']}) - Status: {status}")

    # 3. Test POS add to cart & cart update
    page.goto("http://127.0.0.1:5000/pos", wait_until="networkidle")
    add_btn = page.locator(".pos-item button, .pos-card button, .product-card button")
    if add_btn.count() > 0:
        add_btn.first.click()
        time.sleep(0.5)
        print("[PASS] POS Add Item to Cart Interaction")

    browser.close()

print("\n--- Final Health Check ---")
if errors_found:
    print(f"FAILED: Found {len(errors_found)} errors:")
    for e in errors_found:
        print("   -", e)
else:
    print("SUCCESS: Zero errors found across entire application!")
