from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import QueryRequest, QueryResponse
from retrieval import search
from rag import generate_answer

app = FastAPI(title="wiki-plus-llm")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    hits = search(req.query, top_k=req.top_k)
    answer = generate_answer(req.query, hits)
    sources = [h["payload"] for h in hits] if req.return_sources else []
    return QueryResponse(answer=answer, sources=sources)

# allow your local web UI to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)