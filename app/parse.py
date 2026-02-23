import os

from app.paths import get_browsers_path

browsers_path = get_browsers_path()
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
from playwright.sync_api import sync_playwright, Error


def scrapeTextFromUrl(url, update_status):
        try:
            update_status("🔄 Starting browser...", "#3498db")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Load page and wait for all main network requests
                update_status("🌐 Loading page...", "#3498db")
                page.goto(url)
                page.wait_for_load_state("networkidle")

                update_status("📝 Extracting text...", "#3498db")
                # Scroll to bottom to trigger lazy loading
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_load_state("networkidle")  # wait for new requests

                # Extract visible text
                text_content = page.inner_text("body")

                browser.close()
            
            return text_content

        except Exception as e:
            update_status(f"❌ Error: {str(e)}", "#e74c3c")
            return None