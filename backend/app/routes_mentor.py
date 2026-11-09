from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import mentor
from app.config import settings
from app.database import get_db
from app.models import MentorConversation, Profile, ResumeAnalysis, Roadmap, User
from app.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
    MentorMessageResponse,
    MentorStatus,
    MessageCreate,
    MessageExchange,
)
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/mentor")


def _message_out(message) -> MentorMessageResponse:
    return MentorMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        provider=message.provider,
        notice=message.notice,
        created_at=message.created_at,
    )


def _owned_conversation(db: Session, user: User, conversation_id: str) -> MentorConversation:
    conversation = db.get(MentorConversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _detail(conversation: MentorConversation) -> ConversationDetail:
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[_message_out(m) for m in conversation.messages],
    )


@router.get("/status", response_model=MentorStatus)
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MentorStatus:
    return MentorStatus(
        mode=settings.llm_mode,
        model=settings.groq_model if settings.llm_mode == "groq" else None,
        has_profile=db.query(Profile).filter(Profile.user_id == user.id).first() is not None,
        has_roadmap=db.query(Roadmap).filter(Roadmap.user_id == user.id).first() is not None,
        has_resume=db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user.id, ResumeAnalysis.status == "completed")
        .first()
        is not None,
    )


@router.post("/conversations", response_model=ConversationDetail, status_code=201)
def create_conversation(
    body: ConversationCreate | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    now = datetime.now(UTC)
    title = (body.title.strip() if body and body.title else "") or mentor.DEFAULT_TITLE
    conversation = MentorConversation(user_id=user.id, title=title, created_at=now, updated_at=now)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _detail(conversation)


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    rows = (
        db.query(MentorConversation)
        .filter(MentorConversation.user_id == user.id)
        .order_by(MentorConversation.updated_at.desc())
        .limit(30)
        .all()
    )
    return [
        ConversationSummary(id=c.id, title=c.title, created_at=c.created_at, updated_at=c.updated_at) for c in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ConversationDetail:
    return _detail(_owned_conversation(db, user, conversation_id))


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    db.delete(_owned_conversation(db, user, conversation_id))
    db.commit()


@router.post("/conversations/{conversation_id}/messages", response_model=MessageExchange)
def send_message(
    conversation_id: str,
    body: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageExchange:
    conversation = _owned_conversation(db, user, conversation_id)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    user_msg, assistant_msg = mentor.answer(db, user, conversation, content)
    return MessageExchange(user_message=_message_out(user_msg), assistant_message=_message_out(assistant_msg))
