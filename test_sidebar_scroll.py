from playwright.sync_api import sync_playwright

def test_sidebar():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        
        # 1. Desktop short viewport test (1440 x 600)
        context = browser.new_context(viewport={"width": 1440, "height": 600})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name=username]", "admin")
        page.fill("input[name=password]", "admin123")
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard")
        
        # Check sidebar scrollability
        sidebar_scroll_height = page.evaluate('document.querySelector(".sidebar").scrollHeight')
        sidebar_client_height = page.evaluate('document.querySelector(".sidebar").clientHeight')
        print(f"Desktop sidebar scroll height: {sidebar_scroll_height}, client height: {sidebar_client_height}")
        assert sidebar_scroll_height > sidebar_client_height
        
        # Scroll sidebar to bottom
        page.evaluate('document.querySelector(".sidebar").scrollTop = document.querySelector(".sidebar").scrollHeight')
        page.wait_for_timeout(500)
        page.screenshot(path="audit_screenshots/sidebar_scroll_desktop.png")
        print("Desktop scrolled sidebar screenshot saved.")
        
        # 2. Mobile drawer test (390 x 650)
        page_m = context.new_page()
        page_m.set_viewport_size({"width": 390, "height": 650})
        page_m.goto("http://127.0.0.1:5000/dashboard")
        page_m.wait_for_timeout(500)
        
        # Open drawer
        page_m.click("#sidebar-toggle")
        page_m.wait_for_timeout(500)
        
        # Scroll drawer
        page_m.evaluate('document.querySelector(".sidebar").scrollTop = document.querySelector(".sidebar").scrollHeight')
        page_m.wait_for_timeout(500)
        page_m.screenshot(path="audit_screenshots/sidebar_scroll_mobile.png")
        print("Mobile scrolled drawer screenshot saved.")
        
        # Click logout from sidebar
        logout_btn = page_m.locator('.sidebar-footer a[href="/logout"]')
        assert logout_btn.is_visible()
        logout_btn.click()
        page_m.wait_for_url("**/login")
        print("Successfully logged out via scrollable sidebar button!")
        
        browser.close()
    print("ALL SIDEBAR & LOGOUT SCROLL TESTS PASSED!")

if __name__ == "__main__":
    test_sidebar()
