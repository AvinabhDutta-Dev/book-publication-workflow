from ai_agents.gemini_client import generate
import config

PROMPT = (
    "Rewrite the following chapter to improve its flow and readability without "
    "changing its meaning. Keep the paragraph structure and any dialogue. "
    "Return only the rewritten chapter, with no introduction or commentary.\n\n"
    "{chapter}"
)


def spin_chapter(chapter_text):
    """Rewrite the whole chapter and save it to data/spun_chapter.txt."""
    result = generate(PROMPT.format(chapter=chapter_text))
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "spun_chapter.txt").write_text(result, encoding="utf-8")
    return result
