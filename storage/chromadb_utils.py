"""Durable version storage. ChromaDB writes to storage/chroma_db/, so saved
versions are still there after the process exits."""
import chromadb
from chromadb.config import Settings

import config

COLLECTION_NAME = "book_versions"


def get_collection():
    client = chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(COLLECTION_NAME)


def store_version(id, content, metadata=None):
    """Save (or overwrite) one version. upsert avoids silently dropping a
    re-run that reuses an id."""
    kwargs = {"metadatas": [metadata]} if metadata else {}
    get_collection().upsert(documents=[content], ids=[id], **kwargs)


def search_version(query_text, n_results=1):
    return get_collection().query(query_texts=[query_text], n_results=n_results)
