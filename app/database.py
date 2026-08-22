from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# Some hosted providers still hand out the legacy ``postgres://`` scheme;
# SQLAlchemy 2 expects the explicit driver name.
database_url = (
    DATABASE_URL.replace("postgres://", "postgresql://", 1)
    if DATABASE_URL.startswith("postgres://")
    else DATABASE_URL
)

# SQLite needs check_same_thread=False because FastAPI serves requests from a
# thread pool. Postgres (used when deployed) must not receive that argument.
connect_args = (
    {"check_same_thread": False} if database_url.startswith("sqlite") else {}
)

engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
Base = declarative_base()
