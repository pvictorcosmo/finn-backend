from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.agents.orchestrator import process_message
from app.routers.actions import build_daily_summary

router = APIRouter(tags=["messages"])


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    intent: str
    response: str


@router.post("/message", response_model=MessageResponse)
def handle_message(req: MessageRequest, db: Session = Depends(get_db)):
    result = process_message(req.text, db)
    return MessageResponse(**result)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return {"summary": build_daily_summary(db)}
