from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.cpq_client import CPQClient
from app.openai_client import OpenAIService
from app.utils import summarize_quote_response

app = FastAPI(title="CPQ FastAPI")

cpq = CPQClient()
assistant = OpenAIService()


class PartsCriteria(BaseModel):
    q: str
    limit: int = 1
    offset: int = 0
    totalResults: bool = True


class PartsContext(BaseModel):
    pricebookVarName: Optional[str] = None


class PartsSearchRequest(BaseModel):
    criteria: PartsCriteria
    context: Optional[PartsContext] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@app.get("/")
def root():
    return {"message": "CPQ FastAPI running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/cpq/parts/search")
async def search_parts(payload: PartsSearchRequest):
    try:
        return await cpq.search_parts(payload.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(payload: ChatRequest) -> Dict[str, Any]:
    try:
        return await assistant.chat(payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cpq/quotes/{transaction_id}/summary")
async def quote_summary(transaction_id: str) -> Dict[str, Any]:
    try:
        raw = await cpq.get_quote_summary(transaction_id)
        return summarize_quote_response(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
