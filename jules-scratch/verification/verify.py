from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8088")
    page.screenshot(path="jules-scratch/verification/home.png")

    # Create a new box to ensure there is at least one
    page.get_by_placeholder("📦 Neue Box anlegen").fill("Test Box")
    page.get_by_role("button", name="➕ Box hinzufügen").click()
    page.wait_for_load_state("networkidle")

    # Navigate to the box page
    page.get_by_role("link", name="Test Box").click()
    page.wait_for_load_state("networkidle")
    page.screenshot(path="jules-scratch/verification/box.png")

    browser.close()
