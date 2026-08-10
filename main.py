from scraping.scraper import fetch_content_and_screenshot
from ai_agents.ai_writer import spin_chapter
from ai_agents.ai_reviewer import review_text
from ai_agents.human_in_loop import get_human_feedback
from storage.chromadb_utils import store_version
import os

def main():
    # Step 1: Scrape
    url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
    text = fetch_content_and_screenshot(url, "screenshots/chapter1.png")
    
    # Save scraped text
    with open("chapter1.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Step 2: AI Writer
    spun = spin_chapter(text)

    # Step 3: AI Reviewer
    reviewed = review_text(spun)

    # Step 4: Human-in-the-loop
    final_version = get_human_feedback(reviewed)

    # Step 5: Store final version
    store_version("chapter1_final", final_version)

    print("\n✅ Pipeline completed successfully.")

    final_path = os.path.join("data", "final_chapter.txt")

    with open(final_path, "w", encoding="utf-8") as f:
        f.write("=== Original Chapter ===\n\n")
        f.write(text + "\n\n")
    
        f.write("=== AI-Spun Chapter ===\n\n")
        f.write(spun + "\n\n")
    
        f.write("=== Reviewed Chapter ===\n\n")
        f.write(reviewed + "\n\n")

        f.write("=== Human Suggestion ===\n\n")
        f.write(final_version + "\n")


if __name__ == "__main__":
    main()

