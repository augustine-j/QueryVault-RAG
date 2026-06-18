from fastapi import FastAPI,status,Depends,HTTPException
from typing import List
from app.routers.ask import router  as ask_router
from app.database import engine,Base
from app.models.query_log import QueryLog
from app.routers.analytics import router as analytics_router
from app.routers.ingest import router as ingest_router

Base.metadata.create_all(bind=engine)



app = FastAPI()

app.include_router(ask_router)
app.include_router(analytics_router)
app.include_router(ingest_router)

@app.get("/",status_code=status.HTTP_200_OK)
def main():
    return {"message":"Rag Api Running"}