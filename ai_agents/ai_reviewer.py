from ai_agents.gemini_client import generate
import config

REVIEW_PROMPT = (
    "Review and enhance the following rewritten chapter. Fix grammar and improve "
    "clarity, but preserve the meaning. Return only the improved chapter, with no "
    "introduction or commentary.\n\n{chapter}"
)

REVISE_PROMPT = (
    "You are an editor revising a book chapter. Apply the human reviewer's "
    "feedback below to the chapter. Leave everything the feedback does not "
    "mention unchanged. Return only the full revised chapter, with no "
    "introduction or commentary.\n\n"
    "=== Reviewer feedback ===\n{feedback}\n\n"
    "=== Chapter ===\n{chapter}"
)


def review_text(spun_text):
    """First AI review pass; saves data/reviewed_chapter.txt."""
    result = generate(REVIEW_PROMPT.format(chapter=spun_text))
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "reviewed_chapter.txt").write_text(result, encoding="utf-8")
    return result


def revise_text(text, feedback):
    """Apply human feedback to the chapter. Used by the human-in-the-loop step."""
    return generate(REVISE_PROMPT.format(feedback=feedback, chapter=text))
