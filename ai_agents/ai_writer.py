import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def spin_chapter(chapter_text):
    prompt = f"Rewrite the following text to improve its flow and readability without changing the meaning:\n\n{chapter_text[:1500]}"

    response = model.generate_content(prompt)
    with open("data/spun_chapter.txt", "w", encoding="utf-8") as f:
        f.write(response.text)

    return response.text


