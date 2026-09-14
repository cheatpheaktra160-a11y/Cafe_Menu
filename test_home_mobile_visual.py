"""Verify Home Mobile & Desktop Visual Match on fresh port."""
import os
import time
import subprocess
import urllib.request
from playwright.sync_api import sync_playwright

PORT = 5005
BASE_URL = f"http://127.0.0.1:{PORT}"
ARTIFACT_DIR = r"C:\Users\Ackerman\.gemini\antigravity-ide\brain\ab70a133-ef94-4d15-bb91-6f6a35ca2a29"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def start_server():
    py_exe = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(py_exe):
        py_exe = "python"
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    env["FLASK_RUN_PORT"] = str(PORT)
    p = subprocess.Popen([py_exe, "-c", f"from app import app; app.run(port={PORT})"], cwd=os.getcwd(), env=env)
    for _ in range(20):
        try:
            urllib.request.urlopen(f"{BASE_URL}/", timeout=1)
            print(f"Server up on port {PORT}!")
            return p
        except Exception:
            time.sleep(0.3)
    return p

def run_tests():
    server = start_server()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            
            # 1. Test iPhone 13 (390x844)
            context_mobile = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                is_mobile=True,
                has_touch=True
            )
            page_mobile = context_mobile.new_page()
            page_mobile.goto(f"{BASE_URL}/", wait_until="networkidle")
            time.sleep(1)

            # Check for horizontal overflow
            scroll_width = page_mobile.evaluate("document.documentElement.scrollWidth")
            client_width = page_mobile.evaluate("document.documentElement.clientWidth")
            print(f"Mobile (390px): scrollWidth={scroll_width}, clientWidth={client_width}")
            assert scroll_width <= client_width + 1, f"Horizontal overflow on mobile: {scroll_width} > {client_width}"

            # Capture mobile hero screenshot
            mobile_hero_path = os.path.join(ARTIFACT_DIR, "home_mobile_hero.png")
            page_mobile.screenshot(path=mobile_hero_path, full_page=False)
            print(f"Saved mobile hero screenshot: {mobile_hero_path}")

            # Capture full mobile page
            mobile_full_path = os.path.join(ARTIFACT_DIR, "home_mobile_full.png")
            page_mobile.screenshot(path=mobile_full_path, full_page=True)
            print(f"Saved full mobile screenshot: {mobile_full_path}")

            # 2. Test Desktop (1280x800)
            context_desktop = browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page_desktop = context_desktop.new_page()
            page_desktop.goto(f"{BASE_URL}/", wait_until="networkidle")
            time.sleep(1)
            
            desktop_path = os.path.join(ARTIFACT_DIR, "home_desktop.png")
            page_desktop.screenshot(path=desktop_path, full_page=False)
            print(f"Saved desktop screenshot: {desktop_path}")

            browser.close()
            print("All verification steps passed successfully!")
    finally:
        if server:
            server.terminate()

if __name__ == "__main__":
    run_tests()
