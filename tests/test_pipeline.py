"""Offline tests: Gemini and the browser are replaced with stand-ins, so these
check the pipeline logic without an API key or network access.

Run from the project root:  python -m unittest discover -s tests -v
"""
import gc
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import chromadb
from chromadb import EmbeddingFunction
from chromadb.config import Settings

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from ai_agents import ai_reviewer, ai_writer, gemini_client, human_in_loop  # noqa: E402
from storage import chromadb_utils  # noqa: E402
import main as pipeline  # noqa: E402


class HashEmbedding(EmbeddingFunction):
    """Deterministic embedding so tests never download the real model."""

    def __init__(self):
        pass

    def __call__(self, input):
        return [[float((hash(t) >> i) & 7) for i in range(8)] for t in input]

    @staticmethod
    def name():
        return "test-hash-embedding"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return HashEmbedding()


_TEST_CHROMA_CLIENTS = []


def fake_get_collection():
    client = chromadb.PersistentClient(
        path=str(config.CHROMA_DIR), settings=Settings(anonymized_telemetry=False)
    )
    _TEST_CHROMA_CLIENTS.append(client)  # so the test can release it later
    return client.get_or_create_collection(
        chromadb_utils.COLLECTION_NAME, embedding_function=HashEmbedding()
    )


def close_test_chroma_clients():
    """Release ChromaDB's open database files before temp folders are deleted.

    Windows cannot delete a file that is still open, so a client left open
    makes the temporary folder cleanup fail with WinError 32.
    """
    while _TEST_CHROMA_CLIENTS:
        try:
            _TEST_CHROMA_CLIENTS.pop().close()
        except Exception:
            pass
    try:
        from chromadb.api.client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    gc.collect()


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.candidates = []


class FakeGemini:
    def __init__(self):
        self.prompts = []
        self.models = self

    def generate_content(self, model, contents):
        self.prompts.append(contents)
        return FakeResponse("REWRITTEN:" + contents[-20:])


class TempProject(unittest.TestCase):
    def setUp(self):
        # ignore_cleanup_errors: if Windows still holds a database file for a
        # moment, leaving a temp folder behind must not fail the test.
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name)
        patches = [
            mock.patch.object(config, "DATA_DIR", root / "data"),
            mock.patch.object(config, "SCREENSHOT_DIR", root / "screenshots"),
            mock.patch.object(config, "CHROMA_DIR", root / "chroma"),
            mock.patch.object(chromadb_utils, "get_collection", fake_get_collection),
            mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(close_test_chroma_clients)  # runs before tmp.cleanup
        self.root = root
        self.fake = FakeGemini()
        gemini_client._client = self.fake
        self.addCleanup(setattr, gemini_client, "_client", None)


class HumanFeedbackTests(TempProject):
    def test_feedback_is_sent_to_reviser_and_revised_text_returned(self):
        calls = []

        def reviser(text, feedback):
            calls.append((text, feedback))
            return text + " [revised]"

        answers = iter(["make it shorter", ""])
        result = human_in_loop.get_human_feedback(
            "draft", reviser, input_fn=lambda _: next(answers)
        )
        self.assertEqual(calls, [("draft", "make it shorter")])
        self.assertEqual(result, "draft [revised]")  # not the raw feedback
        log = (config.DATA_DIR / "suggestions.txt").read_text()
        self.assertIn("make it shorter", log)

    def test_enter_accepts_without_calling_ai(self):
        reviser = mock.Mock()
        result = human_in_loop.get_human_feedback("draft", reviser, input_fn=lambda _: "")
        self.assertEqual(result, "draft")
        reviser.assert_not_called()

    def test_eof_accepts(self):
        def raise_eof(_):
            raise EOFError

        self.assertEqual(
            human_in_loop.get_human_feedback("draft", mock.Mock(), input_fn=raise_eof), "draft"
        )

    def test_round_limit(self):
        result = human_in_loop.get_human_feedback(
            "a", lambda t, f: t + "!", max_rounds=2, input_fn=lambda _: "again"
        )
        self.assertEqual(result, "a!!")


class FullTextTests(TempProject):
    def test_writer_and_reviewer_send_the_whole_chapter(self):
        chapter = "word " * 3000  # 15,000 chars, far beyond the old 1,500 cut-off
        ai_writer.spin_chapter(chapter)
        ai_reviewer.review_text(chapter)
        self.assertEqual(len(self.fake.prompts), 2)
        for prompt in self.fake.prompts:
            self.assertIn(chapter, prompt)

    def test_revise_prompt_contains_feedback_and_chapter(self):
        ai_reviewer.revise_text("the chapter body", "use simpler words")
        self.assertIn("use simpler words", self.fake.prompts[0])
        self.assertIn("the chapter body", self.fake.prompts[0])

    def test_missing_key_message(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaises(gemini_client.GeminiError) as ctx:
                gemini_client.require_api_key()
        self.assertIn(".env.example", str(ctx.exception))


class EndToEndTests(TempProject):
    def run_main(self, argv, scraper):
        with mock.patch.object(pipeline, "fetch_content_and_screenshot", scraper):
            pipeline.main(argv)

    def test_non_interactive_run_creates_outputs_and_uses_custom_url(self):
        seen = {}

        def scraper(url, image_path):
            seen["url"] = url
            Path(image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(image_path).write_bytes(b"png")
            return "Chapter text. " * 400

        url = "https://example.org/wiki/Other_Chapter"
        self.run_main(["--url", url, "--non-interactive"], scraper)

        self.assertEqual(seen["url"], url)
        for name in ("original_chapter.txt", "spun_chapter.txt", "reviewed_chapter.txt", "final_chapter.txt"):
            self.assertTrue((config.DATA_DIR / name).stat().st_size > 0, name)
        self.assertTrue((config.SCREENSHOT_DIR / "chapter.png").exists())
        stored = fake_get_collection().get()
        self.assertEqual(sorted(m["stage"] for m in stored["metadatas"]), ["final", "reviewed", "spun"])
        self.assertTrue(all(m["source_url"] == url for m in stored["metadatas"]))

    def test_interactive_feedback_reaches_the_model_and_final_file(self):
        def scraper(url, image_path):
            return "Original body text."

        answers = iter(["add a summary", ""])
        with mock.patch("builtins.input", lambda _="": next(answers)):
            self.run_main([], scraper)
        self.assertTrue(any("add a summary" in p for p in self.fake.prompts))
        final = (config.DATA_DIR / "final_chapter.txt").read_text()
        self.assertIn("=== Final Version", final)
        self.assertNotIn("add a summary\n", final.split("=== Final Version")[1])

    def test_missing_key_fails_before_scraping(self):
        scraper = mock.Mock()
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaises(SystemExit) as ctx:
                self.run_main(["--non-interactive"], scraper)
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))
        scraper.assert_not_called()

    def test_bad_url_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_main(["--url", "not-a-url"], mock.Mock())


class PersistenceTest(unittest.TestCase):
    def test_versions_survive_a_process_restart(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            script = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.path.insert(0, {str(ROOT / 'tests')!r})
import config
from pathlib import Path
config.CHROMA_DIR = Path({tmp!r})
from storage import chromadb_utils
from test_pipeline import fake_get_collection
chromadb_utils.get_collection = fake_get_collection
if sys.argv[1] == "write":
    chromadb_utils.store_version("v1", "hello durable world", {{"stage": "final"}})
else:
    print("COUNT=%d" % fake_get_collection().count())
"""
            for mode in ("write", "read"):
                out = subprocess.run(
                    [sys.executable, "-c", script, mode], capture_output=True, text=True
                )
                self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("COUNT=1", out.stdout)


if __name__ == "__main__":
    unittest.main()