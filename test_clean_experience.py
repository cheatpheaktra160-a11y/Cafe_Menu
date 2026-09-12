import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\8c10c3f7-4071-4414-b534-d9f8a605d93e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

console_errors = []

def handle_console(msg):
    if msg.type == "error":
        console_errors.append(msg.text)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.on("console", handle_console)
    page.on("pageerror", lambda err: console_errors.append(str(err)))

    # 1. Clean Home Page
    print("\n--- 1. Testing Clean 2D Home Page ---")
    page.goto("http://127.0.0.1:5000", wait_until="networkidle")
    time.sleep(1)
    
    # Verify Three.js is NOT loaded
    has_three = page.evaluate("() => typeof window.THREE !== 'undefined'")
    print(f"Three.js Removed: {not has_three}")
    
    home_shot = os.path.join(SCREENSHOT_DIR, "20_clean_home.png")
    page.screenshot(path=home_shot, full_page=False)
    print(f"Saved: {home_shot}")

    # 2. Clean Menu Page
    print("\n--- 2. Testing Clean Menu Page ---")
    page.goto("http://127.0.0.1:5000/menu", wait_until="networkidle")
    time.sleep(1)
    menu_shot = os.path.join(SCREENSHOT_DIR, "21_clean_menu.png")
    page.screenshot(path=menu_shot, full_page=False)
    print(f"Saved: {menu_shot}")

    # 3. Clean Product Page
    print("\n--- 3. Testing Clean Product Detail ---")
    page.goto("http://127.0.0.1:5000/menu/1", wait_until="networkidle")
    time.sleep(1)
    prod_shot = os.path.join(SCREENSHOT_DIR, "22_clean_product.png")
    page.screenshot(path=prod_shot, full_page=False)
    print(f"Saved: {prod_shot}")

    # 4. Login & Admin Dashboard
    print("\n--- 4. Testing Login & Dashboard ---")
    page.goto("http://127.0.0.1:5000/login", wait_until="networkidle")
    page.fill("input[name='username']", "admin")
    page.fill("input[name='password']", "admin123")
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    dash_shot = os.path.join(SCREENSHOT_DIR, "23_clean_dashboard.png")
    page.screenshot(path=dash_shot, full_page=False)
    print(f"Saved: {dash_shot}")

    # 5. Clean POS
    print("\n--- 5. Testing POS ---")
    page.goto("http://127.0.0.1:5000/pos", wait_until="networkidle")
    time.sleep(1)
    pos_shot = os.path.join(SCREENSHOT_DIR, "24_clean_pos.png")
    page.screenshot(path=pos_shot, full_page=False)
    print(f"Saved: {pos_shot}")

    browser.close()

print("\n--- Console Check ---")
if console_errors:
    print(f"FAILED: Found {len(console_errors)} console errors:")
    for err in console_errors:
        print("   -", err)
else:
    print("SUCCESS: 0 console errors detected!")
