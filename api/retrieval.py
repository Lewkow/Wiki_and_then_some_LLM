import os, requests
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("TEXT_EMBED_MODEL", "nomic-embed-text")
COLLECTION = os.environ.get("COLLECTION_NAME", "docs_text")

client = QdrantClient(url=QDRANT_URL)

def embed_query(q: str):
    r = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": q},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    if "embedding" in data:
        return data["embedding"]
    embs = data.get("embeddings")
    if isinstance(embs, list) and embs:
        return embs[0] if isinstance(embs[0], list) else embs
    raise RuntimeError(f"Unexpected embed response from Ollama: keys={list(data.keys())}")

def _article_filter():
    return Filter(must=[FieldCondition(key="is_article", match=MatchValue(value=True))])


def search(q: str, top_k: int = 6):
    vec = embed_query(q)
    # Pull more than needed, then post-filter/dedupe
    res = client.search(
        collection_name=COLLECTION,
        query_vector=vec,
        limit=top_k * 8,
        with_payload=True,
        query_filter=_article_filter()
    )
    uniq, out = set(), []
    for pt in res:
        p = pt.payload or {}
        key = (p.get("doc_name"), p.get("chunk_index"))
        if key in uniq:
            continue
        uniq.add(key)
        out.append({"score": float(pt.score), "payload": p})
        if len(out) >= top_k:
            break

    # Title-first fallback for queries that look like a page name
    if len(out) == 0:
        guess = guess_title(q)  # simple title-case guesser
        if guess:
            # fetch by exact title via scroll
            points, _ = client.scroll(
                collection_name=COLLECTION,
                scroll_filter=Filter(must=[
                    FieldCondition(key="doc_name", match=MatchValue(value=guess)),
                    FieldCondition(key="is_article", match=MatchValue(value=True)),
                ]),
                limit=top_k,
                with_payload=True,
                with_vectors=False,
            )
            for pt in points:
                out.append({"score": 1.0, "payload": pt.payload})
    return out

def guess_title(q: str) -> str | None:
    t = q.strip().lower()
    # very simple heuristics; adjust as you like
    if "simple english wikipedia" in t:
        return "Simple English Wikipedia"
    return None