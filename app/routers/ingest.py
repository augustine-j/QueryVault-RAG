from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import crud
from app.config import MAX_UPLOAD_BYTES
from app.dependencies import get_current_user, get_db, rag
from app.extraction import ExtractionError, detect_kind
from app.models.schemas import DocumentOut
from app.models.user import User

router = APIRouter(tags=["documents"])


@router.post("/ingest", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    try:
        kind = detect_kind(file.filename, file.content_type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )

    # The row is created first so its id can prefix the vector ids; it is rolled
    # back if extraction or embedding fails, leaving no orphan document.
    document = crud.create_document(db, user.id, file.filename, kind)
    try:
        chunk_count, kind = rag.ingest(
            user_id=user.id,
            document_id=document.id,
            filename=file.filename,
            data=data,
            content_type=file.content_type,
        )
    except ExtractionError as error:
        crud.delete_document_row(db, document)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        # Embedding can fail after the vector write; best-effort cleanup keeps
        # a retried upload from leaving stale data in the user's namespace.
        try:
            rag.remove(user.id, document.id)
        except Exception:
            pass
        crud.delete_document_row(db, document)
        raise HTTPException(status_code=502, detail=str(error)) from error

    document.kind = kind
    return crud.set_document_chunk_count(db, document, chunk_count)
