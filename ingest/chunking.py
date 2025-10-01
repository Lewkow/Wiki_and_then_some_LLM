import math

def chunk_text(s: str, chunk_size=800, overlap=120):
    s = s.strip()
    if not s:
        return []
    chunks = []
    start = 0
    n = len(s)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = s[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks

