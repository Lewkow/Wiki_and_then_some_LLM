# ingest/embed.py
import os, requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
TEXT_EMBED_MODEL = os.environ.get("TEXT_EMBED_MODEL", "nomic-embed-text")

def embed_text(text: str):
    r = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": TEXT_EMBED_MODEL, "input": text},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()

    # Accept both shapes:
    # {"embedding":[...]}  OR  {"embeddings":[[...], ...]}
    if "embedding" in data:
        return data["embedding"]

    embs = data.get("embeddings")
    if isinstance(embs, list) and embs:
        # some versions wrap in a list-of-lists
        return embs[0] if isinstance(embs[0], list) else embs

    raise RuntimeError(f"Unexpected embed response from Ollama: keys={list(data.keys())}")

