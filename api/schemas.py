from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6
    return_sources: Optional[bool] = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict] = []

