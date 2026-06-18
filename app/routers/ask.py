from fastapi import APIRouter,status,Depends,HTTPException
from app.models.questions import(QuestionRequest,QuestionResponse)
from app.dependencies import (rag,get_db)
import time
from sqlalchemy.orm import Session
from app.store_getQuery import save_query


router = APIRouter()

@router.post("/ask",status_code=status.HTTP_201_CREATED)
def ask_question(request:QuestionRequest,db:Session=Depends(get_db)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    start_time = time.time()
    
    result =rag.ask(request.question)
    answer = result["answer"]
    sources = result["sources"]
    response_time = (time.time() - start_time)

    answer_found = 0 if "could not find" in answer.lower() else 1

    save_query(
        db=db,
        question=request.question,
        answer=answer,
        response_time=response_time,
        answer_found= answer_found

    )
    return QuestionResponse(answer=answer,sources=sources)
    
