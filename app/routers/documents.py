from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_current_user, get_db, rag
from app.models.schemas import DocumentOut
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return crud.list_documents(db, user.id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    document = crud.get_document(db, user.id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Vectors first: a failure here must not leave rows pointing at live vectors.
    rag.remove(user.id, document.id)
    crud.delete_document_row(db, document)
