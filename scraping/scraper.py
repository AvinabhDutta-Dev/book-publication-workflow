import os
import sys

from playwright.sync_api import sync_playwright

import config


def fetch_content_and_screenshot(url, output_image_path, timeout_ms=60_000):
    """Open `url` in headless Chromium, save a full-page screenshot, return the text.

    Prefers the MediaWiki article body (#mw-content-text) so site menus are not
    sent to the AI; falls back to the whole <body> for other sites.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.screenshot(path=str(output_image_path), full_page=True)
            article = page.locator("#mw-content-text")
            if article.count():
                text = article.first.inner_text()
            else:
                text = page.inner_text("body")
        finally:
            browser.close()
    return text.strip()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else config.DEFAULT_URL
    config.ensure_dirs()
    content = fetch_content_and_screenshot(target, config.SCREENSHOT_DIR / "chapter.png")
    (config.DATA_DIR / "original_chapter.txt").write_text(content, encoding="utf-8")
    print(f"Saved {len(content):,} characters to data/original_chapter.txt")
