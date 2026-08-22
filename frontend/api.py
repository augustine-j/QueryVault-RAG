"""Small, failure-tolerant client for the RAG API."""

import os
from typing import Any

import requests
import streamlit as st

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
TIMEOUT_SECONDS = 120


def base_url() -> str:
    """Read the deployment URL from Streamlit secrets or the environment."""
    try:
        return st.secrets.get("API_BASE_URL", os.getenv("API_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
    except FileNotFoundError:
        return os.getenv("API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _headers() -> dict[str, str]:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _request(method: str, path: str, **kwargs: Any) -> tuple[bool, Any]:
    """Return a success flag plus JSON/body, never exposing request exceptions to views."""
    headers = {**_headers(), **kwargs.pop("headers", {})}
    try:
        response = requests.request(
            method,
            f"{base_url()}{path}",
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            **kwargs,
        )
    except requests.RequestException:
        return False, {"detail": "The API is unavailable or waking up. Please try again in a moment."}

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text or f"Request failed ({response.status_code})."}
    return response.ok, payload


def warm_up() -> tuple[bool, Any]:
    return _request("GET", "/")


def register(email: str, password: str, full_name: str) -> tuple[bool, Any]:
    return _request("POST", "/auth/register", json={"email": email, "password": password, "full_name": full_name or None})


def login(email: str, password: str) -> tuple[bool, Any]:
    return _request("POST", "/auth/login", json={"email": email, "password": password})


def me() -> tuple[bool, Any]:
    return _request("GET", "/auth/me")


def conversations() -> tuple[bool, Any]:
    return _request("GET", "/conversations")


def conversation(conversation_id: int) -> tuple[bool, Any]:
    return _request("GET", f"/conversations/{conversation_id}")


def delete_conversation(conversation_id: int) -> tuple[bool, Any]:
    return _request("DELETE", f"/conversations/{conversation_id}")


def documents() -> tuple[bool, Any]:
    return _request("GET", "/documents")


def upload_document(name: str, data: bytes, mime_type: str) -> tuple[bool, Any]:
    return _request("POST", "/ingest", files={"file": (name, data, mime_type)})


def delete_document(document_id: int) -> tuple[bool, Any]:
    return _request("DELETE", f"/documents/{document_id}")


def ask(question: str, conversation_id: int | None, document_id: int | None) -> tuple[bool, Any]:
    return _request(
        "POST",
        "/ask",
        json={"question": question, "conversation_id": conversation_id, "document_id": document_id},
    )
