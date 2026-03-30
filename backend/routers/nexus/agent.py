"""Nexus agent router — graph-agentic Q&A endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    tool_calls: list[dict]
    duration_ms: int


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    """Run the graph-agentic AI to answer a question about clients, deals, and intel."""
    if not body.question.strip():
        raise HTTPException(400, "question cannot be empty")

    from services.nexus.agent import run_agent

    result = run_agent(question=body.question, session_id=body.session_id)
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        tool_calls=result.tool_calls_log,
        duration_ms=result.duration_ms,
    )
