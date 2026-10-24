"""Thin wrapper around the google-genai SDK used by the writer and reviewer."""
import os
import time

from google import genai
from google.genai import errors

import config

# Gemini Flash models accept ~1M input tokens but cap output at 65,536 tokens
# (roughly 250k characters). Warn well before a rewrite could be cut off.
LONG_TEXT_WARNING_CHARS = 150_000

_client = None


class GeminiError(RuntimeError):
    """Raised for problems we can explain to the user in plain language."""


def require_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_api_key_here":
        raise GeminiError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and paste a "
            "key from https://aistudio.google.com/apikey"
        )
    return key


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=require_api_key())
    return _client


def generate(prompt: str, retries: int = 3) -> str:
    """Send one prompt and return the response text.

    Retries rate-limit / overload errors, and raises GeminiError for the
    failures a new user is most likely to hit.
    """
    if len(prompt) > LONG_TEXT_WARNING_CHARS:
        print(
            f"Warning: prompt is {len(prompt):,} characters; the model's output "
            "limit may cut the rewritten text short."
        )
    model = config.gemini_model()
    client = _get_client()

    response = None
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            break
        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            if code in (429, 500, 503) and attempt < retries:
                wait = 2 ** attempt * 2
                print(f"Gemini returned {code}; retrying in {wait}s ({attempt}/{retries - 1})...")
                time.sleep(wait)
                continue
            if code == 404:
                raise GeminiError(
                    f"Gemini model '{model}' was not found. It may have been retired. "
                    "Set GEMINI_MODEL in .env to a current model, see "
                    "https://ai.google.dev/gemini-api/docs/models"
                ) from exc
            if code in (400, 401, 403):
                raise GeminiError(
                    f"Gemini rejected the request ({code}). Check that GEMINI_API_KEY "
                    f"is valid and allowed to use '{model}'. Details: {exc}"
                ) from exc
            raise

    text = response.text if response is not None else None
    if not text:
        raise GeminiError(
            "Gemini returned no text (the response may have been blocked by a "
            "safety filter). Try again or use a different chapter."
        )

    candidates = response.candidates or []
    finish = getattr(candidates[0], "finish_reason", None) if candidates else None
    if getattr(finish, "name", str(finish)) == "MAX_TOKENS":
        raise GeminiError(
            "Gemini's reply was cut off at the output token limit, so the rewritten "
            "chapter would be incomplete. Use a shorter chapter."
        )
    return text.strip()
