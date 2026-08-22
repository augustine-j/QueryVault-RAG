from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, jwt_secret
from app.database import Base, engine

# Imported for their side effect of registering tables on Base.metadata.
from app.models import chat, document, user  # noqa: F401
from app.routers.ask import router as ask_router
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.ingest import router as ingest_router

Base.metadata.create_all(bind=engine)

# Fail fast rather than deploying with an unsigned/guessable token secret.
jwt_secret()

app = FastAPI(
    title="RAG Document Chat API",
    description="Multi-user document chatbot over PDFs and images.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # A wildcard origin cannot be used with credentialed browser requests.
    # The app uses an Authorization header, not cookies, so this is safe locally.
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(documents_router)


@app.get("/", status_code=status.HTTP_200_OK, tags=["health"])
def health():
    """Also serves as the platform health check target."""
    return {"message": "Rag Api Running"}
