def get_human_feedback(spun_text):
    print("\n--- AI Written Chapter ---\n")
    print(spun_text)
    feedback = input("Enter suggestions (or press Enter to accept): ")
    with open("data/suggestions.txt", "a", encoding="utf-8") as f:
        f.write(f"\nSuggestion: {feedback}\n")
    if feedback:
        # Send this back to the AI Reviewer for refining
        return feedback
    return spun_text
