import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("book_versions")

def store_version(id, content):
    collection.add(documents=[content], ids=[id])

def search_version(query_text):
    results = collection.query(query_texts=[query_text], n_results=1)
    return results
