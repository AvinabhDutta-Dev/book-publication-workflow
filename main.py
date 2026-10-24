import argparse
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import config
from ai_agents.ai_reviewer import review_text, revise_text
from ai_agents.ai_writer import spin_chapter
from ai_agents.gemini_client import GeminiError, require_api_key
from ai_agents.human_in_loop import get_human_feedback
from scraping.scraper import fetch_content_and_screenshot
from storage.chromadb_utils import store_version


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Scrape a chapter, rewrite and review it with Gemini, "
        "collect human feedback, and store every version."
    )
    parser.add_argument(
        "--url",
        default=config.DEFAULT_URL,
        help="Chapter page to process (default: The Gates of Morning, Book 1, Chapter 1)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip the human feedback step and accept the AI-reviewed text",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        help="Maximum human feedback rounds (default: 3)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if urlparse(args.url).scheme not in ("http", "https"):
        sys.exit(f"Error: --url must start with http:// or https:// (got {args.url!r})")

    try:
        require_api_key()  # fail fast, before opening a browser
        config.ensure_dirs()

        # Step 1: Scrape
        print(f"[1/5] Scraping {args.url}")
        text = fetch_content_and_screenshot(args.url, config.SCREENSHOT_DIR / "chapter.png")
        (config.DATA_DIR / "original_chapter.txt").write_text(text, encoding="utf-8")
        if not text:
            sys.exit("Error: the page had no readable text.")

        # Step 2: AI Writer
        print("[2/5] AI writer is rewriting the chapter...")
        spun = spin_chapter(text)

        # Step 3: AI Reviewer
        print("[3/5] AI reviewer is polishing it...")
        reviewed = review_text(spun)

        # Step 4: Human-in-the-loop (feedback goes back to the AI reviewer)
        if args.non_interactive:
            print("[4/5] Skipping human feedback (--non-interactive)")
            final_version = reviewed
        else:
            print("[4/5] Human review")
            final_version = get_human_feedback(reviewed, revise_text, args.max_rounds)

        # Step 5: Store every version durably
        print("[5/5] Saving versions to ChromaDB")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for stage, content in (("spun", spun), ("reviewed", reviewed), ("final", final_version)):
            store_version(
                f"{run_id}_{stage}",
                content,
                {"stage": stage, "source_url": args.url, "run_id": run_id},
            )
    except GeminiError as exc:
        sys.exit(f"Error: {exc}")

    with open(config.DATA_DIR / "final_chapter.txt", "w", encoding="utf-8") as f:
        f.write("=== Original Chapter ===\n\n" + text + "\n\n")
        f.write("=== AI-Spun Chapter ===\n\n" + spun + "\n\n")
        f.write("=== Reviewed Chapter ===\n\n" + reviewed + "\n\n")
        f.write("=== Final Version (after human feedback) ===\n\n" + final_version + "\n")

    print("\nPipeline completed successfully. Outputs are in data/ and screenshots/.")


if __name__ == "__main__":
    main()
