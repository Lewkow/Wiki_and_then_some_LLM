# ingest/ingest.py
import os, uuid, json, glob, time
from pathlib import Path
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from chunking import chunk_text
from parsers import load_any
from embed import embed_text
from wiki_stream import iter_pages, guess_wiki_base

import re
import hashlib

def is_article_title(title: str) -> bool:
    # Skip namespaces like "Wikipedia:", "Category:", "Talk:", etc.
    return ":" not in title

def clean_snippet(s: str, n=500):
    # strip wikilinks & templates for nicer RAG context
    s = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]+\}\}", "", s)
    return re.sub(r"\s+", " ", s).strip()[:n]

def make_id(*parts) -> int:
    h = hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:16], 16)  # stable 64-bit-ish

WIKI_LINK = re.compile(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]")
TEMPLATES = re.compile(r"\{\{[^}]+\}\}")
def clean_snippet(s: str, n=500):
    s = WIKI_LINK.sub(r"\1", s)
    s = TEMPLATES.sub("", s)
    return re.sub(r"\s+", " ", s).strip()[:n]

QDRANT_URL   = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION   = os.environ.get("COLLECTION_NAME", "docs_text")
CHUNK_SIZE   = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP= int(os.environ.get("CHUNK_OVERLAP", "120"))

DATA_DIR     = Path("/app/data/user_docs")
WIKI_GLOB    = os.environ.get("WIKI_DUMP_GLOB", "/app/data/wikipedia/*pages-articles-multistream*.xml*")
MAX_WIKI_PAGES = int(os.environ.get("MAX_WIKI_PAGES", "0"))  # 0 = no limit

def wait_for_ollama():
    import requests
    base = os.environ.get("OLLAMA_URL","http://localhost:11434")
    for _ in range(60):
        try:
            r = requests.get(f"{base}/api/tags", timeout=5)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("Ollama not ready")

def ensure_collection(client, dim: int):
    from qdrant_client.models import Distance, VectorParams
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def upsert_batch(client: QdrantClient, batch):
    if batch:
        client.upsert(collection_name=COLLECTION, points=batch)
        batch.clear()

def embed_chunks(text: str):
    for ch in chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP):
        yield embed_text(ch), ch

def ingest_user_docs(client: QdrantClient):
    points = []
    for path in tqdm(sorted(DATA_DIR.rglob("*")), desc="user_docs"):
        if not path.is_file():
            continue
        text = load_any(path)
        if not text.strip():
            continue
        for i, (vec, ch) in enumerate(embed_chunks(text)):
            pid = int(uuid.uuid4().int % (10**18))
            payload = {
                "source": "user",
                "path": str(path),
                "chunk_index": i,
                "doc_name": path.name,
                "modality": "text",
                "snippet": ch[:500],
            }
            points.append(PointStruct(id=pid, vector=vec, payload=payload))
            if len(points) >= 256:
                upsert_batch(client, points)
    upsert_batch(client, points)

def ingest_wikipedia(client: QdrantClient):
    dumps = sorted(glob.glob(WIKI_GLOB))
    if not dumps:
        print(f"No WIKI dumps found (WIKI_DUMP_GLOB={WIKI_GLOB})")
        return
    for dp in dumps:
        print(f"Found dump: {dp}")
        base = guess_wiki_base(dp)
        points, n_pages, n_chunks = [], 0, 0

        for title, text in tqdm(iter_pages(Path(dp)), desc=f"wiki:{Path(dp).name}"):
            if not is_article_title(title):
                continue  # drop "Wikipedia:" etc.
            n_pages += 1
            if MAX_WIKI_PAGES and n_pages > MAX_WIKI_PAGES:
                break
            url = base + title.replace(" ", "_")
            for i, (vec, ch) in enumerate(embed_chunks(text)):
                n_chunks += 1
                pid = make_id("wikipedia", title, i)  # stable ID -> no dupes on re-ingest
                points.append(PointStruct(
                    id=pid,
                    vector=vec,
                    payload={
                        "source": "wikipedia",
                        "title": title,
                        "url": url,
                        "doc_name": title,
                        "chunk_index": i,
                        "modality": "text",
                        "snippet": clean_snippet(ch),
                        "is_article": True,   # helpful for filtering at query time
                    },
                ))
                if len(points) >= 256:
                    upsert_batch(client, points)
        upsert_batch(client, points)
        print(json.dumps({"dump": dp, "pages": n_pages, "chunks": n_chunks}))

def main():
    # Ensure Ollama is ready (prevents early 404s/timeouts on /api/embed)
    wait_for_ollama()

    # warm-up to detect embedding dimensionality
    dim = len(embed_text("warmup"))
    client = QdrantClient(url=QDRANT_URL)
    ensure_collection(client, dim)

    # ingest user-provided docs first, then Wikipedia dump
    ingest_user_docs(client)
    ingest_wikipedia(client)

    print(json.dumps({"status": "ok", "collection": COLLECTION}))

if __name__ == "__main__":
    main()
