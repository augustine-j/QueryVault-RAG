"""Offline regression tests for auth, conversation isolation, and documents."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

# These are deliberately set before importing the app: configuration is read once
# at startup, just as it is in a deployed process.
os.environ["JWT_SECRET"] = "test-secret-that-is-long-and-not-for-production"
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(tempfile.gettempdir()) / f'rag-api-{uuid4()}.db').as_posix()}"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.routers import ask as ask_router
from app.routers import documents as documents_router
from app.routers import ingest as ingest_router


class FakeRag:
    def __init__(self):
        self.deleted: list[tuple[int, int]] = []

    def ingest(self, user_id, document_id, filename, data, content_type):
        kind = "pdf" if filename.lower().endswith(".pdf") else "image"
        return 1, kind

    def ask(self, user_id, question, document_id=None, history=None):
        return {
            "answer": f"Answer: {question}",
            "sources": [{"chunk_id": 0, "text": "Offline source", "filename": "test.pdf", "score": 0.9}],
        }

    def remove(self, user_id, document_id):
        self.deleted.append((user_id, document_id))


@pytest.fixture(autouse=True)
def clean_database(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    fake = FakeRag()
    monkeypatch.setattr(ask_router, "rag", fake)
    monkeypatch.setattr(ingest_router, "rag", fake)
    monkeypatch.setattr(documents_router, "rag", fake)
    yield fake
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def register(client, email="person@example.com"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "correct-horse-battery", "full_name": "Person"},
    )
    assert response.status_code == 201
    return response.json()


def authorization(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_duplicate_login_and_unauthenticated_route(client):
    account = register(client)
    assert account["user"]["email"] == "person@example.com"
    assert client.post("/auth/register", json={"email": "person@example.com", "password": "correct-horse-battery"}).status_code == 409
    assert client.post("/auth/login", json={"email": "person@example.com", "password": "wrong-password"}).status_code == 401
    assert client.get("/conversations").status_code == 401


def test_ask_creates_and_then_appends_to_a_thread(client):
    token = register(client)["access_token"]
    headers = authorization(token)
    first = client.post("/ask", headers=headers, json={"question": "What is covered?"})
    assert first.status_code == 201
    conversation_id = first.json()["conversation_id"]
    assert first.json()["conversation_title"] == "What is covered?"

    detail = client.get(f"/conversations/{conversation_id}", headers=headers).json()
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]

    second = client.post("/ask", headers=headers, json={"question": "And exclusions?", "conversation_id": conversation_id})
    assert second.status_code == 201
    assert second.json()["conversation_id"] == conversation_id
    listed = client.get("/conversations", headers=headers).json()
    assert len(listed) == 1
    assert listed[0]["message_count"] == 4


def test_conversations_are_private(client):
    first_token = register(client, "first@example.com")["access_token"]
    second_token = register(client, "second@example.com")["access_token"]
    created = client.post("/ask", headers=authorization(first_token), json={"question": "Private question"}).json()

    assert client.get(f"/conversations/{created['conversation_id']}", headers=authorization(second_token)).status_code == 404
    assert client.get("/conversations", headers=authorization(second_token)).json() == []


def test_ingest_accepts_pdf_and_image_and_rejects_text(client):
    token = register(client)["access_token"]
    headers = authorization(token)
    pdf = client.post("/ingest", headers=headers, files={"file": ("one.pdf", b"%PDF-test", "application/pdf")})
    image = client.post("/ingest", headers=headers, files={"file": ("note.png", b"png", "image/png")})
    text = client.post("/ingest", headers=headers, files={"file": ("note.txt", b"hello", "text/plain")})
    assert pdf.status_code == 201
    assert image.status_code == 201
    assert text.status_code == 400


def test_deleting_document_removes_vectors_and_row(client, clean_database):
    token = register(client)["access_token"]
    headers = authorization(token)
    created = client.post("/ingest", headers=headers, files={"file": ("one.pdf", b"%PDF-test", "application/pdf")}).json()
    assert client.delete(f"/documents/{created['id']}", headers=headers).status_code == 204
    assert client.get("/documents", headers=headers).json() == []
    assert clean_database.deleted == [(1, created["id"])]
