from playwright.sync_api import sync_playwright, TimeoutError
from bs4 import BeautifulSoup
import re


def scrapeTextFromUrl(url, update_status):
    """
    Hybrid scraper:
    1) Try visible-text extraction with DOM stabilization
    2) Fallback to BeautifulSoup on main-frame HTML
    """
    timeout_ms=15000

    def primary_method(page):
        # Load skeleton
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait for real text to exist
        page.wait_for_function(
            "document.body && document.body.innerText.length > 500",
            timeout=timeout_ms
        )

        # Trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        # Wait for DOM text to stabilize
        page.wait_for_function("""
            () => {
                const len = document.body.innerText.length;
                if (!window.__prevLen) {
                    window.__prevLen = len;
                    return false;
                }
                if (window.__prevLen === len) {
                    return true;
                }
                window.__prevLen = len;
                return false;
            }
        """, timeout=5000)

        return page.inner_text("body")

    def fallback_method(page):
        # Get main-frame HTML only
        html = page.content()

        soup = BeautifulSoup(html, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator=" ")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    try:
        update_status("🔄 Starting browser...", "#3498db")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                update_status("🌐 Loading page (primary method)...", "#3498db")
                text = primary_method(page)
                browser.close()

                update_status("✅ Extracted visible text", "#2ecc71")
                return text

            except TimeoutError:
                update_status("⏱️ Primary method timed out — falling back...", "#f39c12")
                text = fallback_method(page)
                browser.close()

                update_status("✅ Extracted text via fallback method", "#f39c12")
                return text

            except Exception:
                # Any unexpected primary failure → fallback
                update_status("⚠️ Primary failed — falling back...", "#f39c12")
                text = fallback_method(page)
                browser.close()
                update_status("✅ Extracted text via fallback method", "#f39c12")
                return text

    except Exception as e:
        update_status(f"❌ Error: {str(e)}", "#e74c3c")
        return None
