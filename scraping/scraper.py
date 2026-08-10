from playwright.sync_api import sync_playwright
import os

def fetch_content_and_screenshot(url, output_image_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=output_image_path, full_page=True)
        content = page.content()
        text = page.inner_text("body")
        browser.close()
        return text

if __name__ == "__main__":
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    os.makedirs("screenshots", exist_ok=True)
    text = fetch_content_and_screenshot(url, "screenshots/chapter1.png")
    with open("chapter1.txt", "w", encoding="utf-8") as f:
        f.write(text)
