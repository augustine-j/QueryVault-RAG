from app.config import EMBEDDING_DIMENSION, EMBEDDING_MODEL
from app.gemini_client import get_client
from google.genai import types


def embed(text: str) -> list[float]:
    try:
        response = get_client().models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=EMBEDDING_DIMENSION
            ),
        )
        return response.embeddings[0].values
    except Exception as error:
        raise RuntimeError(f"Gemini embedding request failed: {error}") from error


def create_embeddings(chunks: list[str]) -> list[list[float]]:
    return [embed(f"title:none | text:{chunk}") for chunk in chunks]


def create_query_embedding(question: str) -> list[float]:
    return embed(f"task:question answering | Query: {question}")
