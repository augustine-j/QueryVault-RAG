import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_current_user, get_db, rag
from app.models.schemas import AskRequest, AskResponse
from app.models.user import User

router = APIRouter(tags=["chat"])


@router.post("/ask", response_model=AskResponse, status_code=status.HTTP_201_CREATED)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if request.document_id is not None and not crud.get_document(
        db, user.id, request.document_id
    ):
        raise HTTPException(status_code=404, detail="Document not found")

    if request.conversation_id is None:
        conversation = crud.create_conversation(
            db, user.id, crud.title_from_question(question)
        )
        history: list[dict] = []
    else:
        conversation = crud.get_conversation(db, user.id, request.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history = crud.get_recent_history(db, conversation.id)

    start_time = time.time()
    try:
        result = rag.ask(
            user_id=user.id,
            question=question,
            document_id=request.document_id,
            history=history,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    response_time = time.time() - start_time

    crud.add_message(db, conversation, "user", question)
    crud.add_message(
        db,
        conversation,
        "assistant",
        result["answer"],
        sources=result["sources"],
        response_time=response_time,
    )
    crud.touch_conversation(db, conversation)

    return AskResponse(
        conversation_id=conversation.id,
        conversation_title=conversation.title,
        answer=result["answer"],
        sources=result["sources"],
        response_time=response_time,
    )
