"""Shared settings. All paths are anchored to the project root, so the
pipeline behaves the same no matter which directory you launch it from."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"
CHROMA_DIR = PROJECT_ROOT / "storage" / "chroma_db"

DEFAULT_URL = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"

# Google retires Gemini models every few months. Override with GEMINI_MODEL in
# .env instead of editing code. "gemini-flash-latest" is Google's moving alias.
DEFAULT_MODEL = "gemini-3.8-flash"


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
