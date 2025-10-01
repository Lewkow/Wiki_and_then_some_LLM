import os, requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
GEN_MODEL = os.environ.get("GENERATION_MODEL", "llama3.1:8b-instruct")

SYS_PROMPT = "You are a concise assistant. If sources are provided, cite the filenames inline like [source: <doc_name>]. Be accurate and brief."

def build_prompt(query: str, contexts):
    ctx_lines = []
    for i, c in enumerate(contexts, 1):
        p = c["payload"]
        name = p.get("doc_name", "unknown")
        url  = p.get("url", p.get("path",""))
        snip = p.get("snippet","")
        score= c.get("score", 0.0)
        ctx_lines.append(f"[{i}] {name} (score={score:.3f})\n{snip}\nSource: {url}")
    context_block = "\n\n".join(ctx_lines)
    return (
      f"{SYS_PROMPT}\n\n"
      f"### Context\n{context_block}\n\n"
      f"### Task\nAnswer using only the context above. "
      f"Cite the source as [source: <doc_name>].\n"
      f"### Query\n{query}\n"
      f"### Answer\n"
    )

def generate_answer(query: str, contexts):
    # For brevity we don't fetch the full text again; this MVP just cites doc names.
    prompt = build_prompt(query, contexts)
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                      json={"model": GEN_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return r.json()["response"]

