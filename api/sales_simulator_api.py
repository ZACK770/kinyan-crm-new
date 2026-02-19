"""
Sales Simulator API — AI-powered sales training chat.
Prefix: /api/sales-simulator
"""
from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user
from db.models import User

router = APIRouter()


class SimulatorMessage(BaseModel):
    role: str  # "salesperson" or "customer"
    content: str


class SimulatorChatRequest(BaseModel):
    messages: List[SimulatorMessage]


class SimulatorChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=SimulatorChatResponse)
async def simulator_chat(
    body: SimulatorChatRequest,
    user: User = Depends(get_current_user),
):
    """Send conversation history and get AI customer response."""
    from services.sales_simulator import chat_with_simulator

    if not body.messages:
        raise HTTPException(400, "נדרשת לפחות הודעה אחת")

    messages_dicts = [{"role": m.role, "content": m.content} for m in body.messages]

    try:
        response_text = await chat_with_simulator(messages_dicts)
        return {"response": response_text}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"שגיאה בתקשורת עם AI: {str(e)}")
