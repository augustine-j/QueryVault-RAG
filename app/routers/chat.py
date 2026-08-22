from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_current_user, get_db
from app.models.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    ConversationRename,
)
from app.models.user import User

router = APIRouter(prefix="/conversations", tags=["chat"])


def _load(db: Session, user: User, conversation_id: int):
    conversation = crud.get_conversation(db, user.id, conversation_id)
    if conversation is None:
        # 404 rather than 403: another user's thread should not even be confirmed
        # to exist.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return crud.list_conversations(db, user.id)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_conversation(db, user.id, payload.title)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = _load(db, user, conversation_id)
    messages = crud.get_messages(db, conversation.id)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": len(messages),
        "messages": [crud.serialize_message(message) for message in messages],
    }


@router.patch("/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: int,
    payload: ConversationRename,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = _load(db, user, conversation_id)
    return crud.rename_conversation(db, conversation, payload.title)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    crud.delete_conversation(db, _load(db, user, conversation_id))
