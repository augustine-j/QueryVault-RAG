"""Lazily created Gemini client shared by generation, embedding, and vision."""

from functools import lru_cache

from google import genai

from app.config import gemini_api_key


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    return genai.Client(api_key=gemini_api_key())
