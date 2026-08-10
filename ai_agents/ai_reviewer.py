import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def review_text(spun_text):
    prompt = f"Review and enhance the following rewritten chapter. Fix grammar, improve clarity, but preserve meaning:\n\n{spun_text[:1500]}"
    response = model.generate_content(prompt)
    with open("data/reviewed_chapter.txt", "w", encoding="utf-8") as f:
        f.write(response.text)

    return response.text
