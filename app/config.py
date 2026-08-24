"""Central configuration.

Every environment variable the app needs is read here once, so a missing key
produces one clear error instead of an import-time KeyError deep in a module.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "See .env.example for the full list."
        )
    return value


# Database: SQLite locally, Postgres (Neon/Supabase) when deployed.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag.db")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIMENSION = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "768"))

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST", "")

# Auth
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))

# Retrieval / upload limits
TOP_K = int(os.getenv("TOP_K", "5"))
SEARCH_FALLBACK = os.getenv("ENABLE_SEARCH_FALLBACK", "true").strip().lower() in {
    "1",
    "true",
    "yes",
}
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "6"))

# CORS: comma-separated list, "*" allows everything.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]


def jwt_secret() -> str:
    """Resolved lazily so importing the app without a secret still works in tests."""
    return _require("JWT_SECRET")


def gemini_api_key() -> str:
    return _require("GEMINI_API_KEY")


def pinecone_api_key() -> str:
    return _require("PINECONE_API_KEY")


def pinecone_index_host() -> str:
    return _require("PINECONE_INDEX_HOST")
