from fastapi import APIRouter,File,UploadFile,HTTPException,status
import shutil
from pathlib import Path
from app.dependencies import rag

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)
router = APIRouter()



@router.post("/ingest",status_code=status.HTTP_202_ACCEPTED)

async def upload_file(file:UploadFile=File(...)):
    if file.filename == "":
        raise HTTPException(status_code=400, detail="No file selected")
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
        status_code=400,
        detail="Only PDF files are allowed"
    )
    file_path = UPLOAD_DIR / file.filename

    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

        rag.ingest_pdf(file_path)

    return {
        "message":"Document uploaded sucessfully",
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "location": str(file_path)
    }

