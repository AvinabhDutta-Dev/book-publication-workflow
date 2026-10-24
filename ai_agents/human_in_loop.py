from datetime import datetime, timezone

import config


def _log_suggestion(feedback):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(config.DATA_DIR / "suggestions.txt", "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {feedback}\n")


def get_human_feedback(text, reviser, max_rounds=3, input_fn=None):
    """Show the chapter, collect suggestions, and send them back to the AI.

    `reviser(text, feedback)` returns the revised chapter (ai_reviewer.revise_text).
    Press Enter on an empty prompt to accept the current version. Returns the
    final chapter text, never the raw feedback.
    """
    ask = input_fn or input
    for round_number in range(1, max_rounds + 1):
        print(f"\n--- Chapter (review round {round_number}/{max_rounds}) ---\n")
        print(text)
        try:
            feedback = ask(
                "\nEnter suggestions for the AI reviewer (or press Enter to accept): "
            ).strip()
        except EOFError:  # no terminal attached: accept as-is
            print("\nNo input available; accepting the current version.")
            return text
        if not feedback:
            return text
        _log_suggestion(feedback)
        print("\nSending your suggestions to the AI reviewer...")
        text = reviser(text, feedback)

    print(f"\nReached the limit of {max_rounds} feedback rounds; keeping the latest version.")
    return text
