from app.rag_service import RAGService
from sqlalchemy.orm import session
from app.database import SessionLocal


rag = RAGService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

