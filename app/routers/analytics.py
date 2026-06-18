from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.store_getQuery import get_analytics

router =APIRouter()

@router.get("/analytics",status_code=status.HTTP_200_OK)
def analytics(db:Session=Depends(get_db)):
    return get_analytics(db)

