import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\8c10c3f7-4071-4414-b534-d9f8a605d93e"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

console_errors = []
console_logs = []

def handle_console(msg):
    if msg.type == "error":
        console_errors.append(msg.text)
    console_logs.append(f"[{msg.type}] {msg.text}")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.on("console", handle_console)
    page.on("pageerror", lambda err: console_errors.append(str(err)))

    print("\n--- 1. Testing 3D Home Page ---")
    page.goto("http://127.0.0.1:5000", wait_until="networkidle")
    time.sleep(2) # Allow 3D animation loop to render multiple frames

    # Verify Three.js loaded
    has_three = page.evaluate("() => typeof window.THREE !== 'undefined'")
    print(f"Three.js Loaded: {has_three}")

    # Check 3D Canvas element
    canvas_count = page.locator(".coffee-3d-canvas").count()
    print(f"Coffee 3D Canvas elements found: {canvas_count}")

    # Check Ambient Canvas
    bg_canvas_count = page.locator("#ambient-3d-bg canvas").count()
    print(f"Ambient Background Canvas found: {bg_canvas_count}")

    # Take high-res screenshot of 3D Home
    home_shot = os.path.join(SCREENSHOT_DIR, "10_3d_home_hero.png")
    page.screenshot(path=home_shot, full_page=False)
    print(f"Saved: {home_shot}")

    # Hover over 3D canvas and cards
    page.mouse.move(900, 350)
    time.sleep(1)
    page.mouse.move(950, 250)
    time.sleep(1)

    print("\n--- 2. Testing 3D Product Detail Customizer ---")
    page.goto("http://127.0.0.1:5000/menu/1", wait_until="networkidle")
    time.sleep(1.5)

    # Click 3D View toggle
    btn_3d = page.locator("#btn-view-3d")
    if btn_3d.count() > 0:
        btn_3d.click()
        time.sleep(1.5)
        print("Clicked 3D View button")

    # Select Large size
    page.select_option("select[name='size']", "Large")
    time.sleep(1)
    print("Selected size: Large")

    prod_shot = os.path.join(SCREENSHOT_DIR, "11_3d_product_customizer.png")
    page.screenshot(path=prod_shot, full_page=False)
    print(f"Saved: {prod_shot}")

    print("\n--- 3. Testing Menu Page ---")
    page.goto("http://127.0.0.1:5000/menu", wait_until="networkidle")
    time.sleep(1)
    menu_shot = os.path.join(SCREENSHOT_DIR, "12_3d_menu.png")
    page.screenshot(path=menu_shot, full_page=False)
    print(f"Saved: {menu_shot}")

    browser.close()

print("\n--- Console Errors Check ---")
if console_errors:
    print(f"FAILED: Found {len(console_errors)} console errors:")
    for err in console_errors:
        print("   -", err)
else:
    print("SUCCESS: 0 console errors detected!")

print("\nVerification Complete.")
