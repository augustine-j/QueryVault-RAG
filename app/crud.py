"""Database access for users, conversations, messages and documents."""

import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import HISTORY_TURNS
from app.models.chat import Conversation, Message
from app.models.document import Document
from app.models.user import User
from app.security import hash_password

TITLE_MAX_LENGTH = 60


# --- users --------------------------------------------------------------------


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email.lower()).first()


def create_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    user = User(
        email=email.lower(),
        full_name=full_name,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- conversations ------------------------------------------------------------


def title_from_question(question: str) -> str:
    title = " ".join(question.strip().split())
    if len(title) <= TITLE_MAX_LENGTH:
        return title or "New chat"
    return title[:TITLE_MAX_LENGTH].rstrip() + "…"


def create_conversation(db: Session, user_id: int, title: str) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation | None:
    """Scoped by user_id, so another user's id simply does not exist here."""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )


def list_conversations(db: Session, user_id: int) -> list[dict]:
    counts = dict(
        db.query(Message.conversation_id, func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .filter(Conversation.user_id == user_id)
        .group_by(Message.conversation_id)
        .all()
    )
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )
    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "message_count": counts.get(conversation.id, 0),
        }
        for conversation in conversations
    ]


def delete_conversation(db: Session, conversation: Conversation) -> None:
    db.delete(conversation)
    db.commit()


def rename_conversation(db: Session, conversation: Conversation, title: str) -> Conversation:
    conversation.title = title
    db.commit()
    db.refresh(conversation)
    return conversation


def touch_conversation(db: Session, conversation: Conversation) -> None:
    """Bump updated_at so the sidebar orders threads by last activity.

    Adding a message does not modify the conversation row, so `onupdate` never
    fires on its own.
    """
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()


# --- messages -----------------------------------------------------------------


def add_message(
    db: Session,
    conversation: Conversation,
    role: str,
    content: str,
    sources: list[dict] | None = None,
    response_time: float | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        sources=json.dumps(sources) if sources else None,
        response_time=response_time,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def serialize_message(message: Message) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "sources": json.loads(message.sources) if message.sources else [],
        "response_time": message.response_time,
        "created_at": message.created_at,
    }


def get_messages(db: Session, conversation_id: int) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id)
        .all()
    )


def get_recent_history(db: Session, conversation_id: int, turns: int = HISTORY_TURNS) -> list[dict]:
    """The last `turns` messages, oldest first, as {role, content} dicts."""
    recent = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(turns)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in reversed(recent)]


# --- documents ----------------------------------------------------------------


def create_document(db: Session, user_id: int, filename: str, kind: str) -> Document:
    document = Document(user_id=user_id, filename=filename, kind=kind, chunk_count=0)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def set_document_chunk_count(db: Session, document: Document, chunk_count: int) -> Document:
    document.chunk_count = chunk_count
    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session, user_id: int) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.id.desc())
        .all()
    )


def get_document(db: Session, user_id: int, document_id: int) -> Document | None:
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == user_id)
        .first()
    )


def delete_document_row(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()
