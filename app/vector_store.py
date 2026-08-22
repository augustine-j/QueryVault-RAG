"""Pinecone access, isolated per user.

Each user's vectors live in their own namespace (`user-<id>`), and every vector
carries the owning `document_id` in metadata plus an ID prefixed with it
(`<document_id>#chunk-<n>`). That gives per-user isolation, per-document filtering
on query, and per-document deletion without touching anyone else's data.
"""

from functools import lru_cache

from pinecone import Pinecone
from pinecone.exceptions import NotFoundException

from app.config import TOP_K, pinecone_api_key, pinecone_index_host

BATCH_SIZE = 100

@lru_cache(maxsize=1)
def get_index():
    pc = Pinecone(api_key=pinecone_api_key())
    return pc.Index(host=pinecone_index_host())


def namespace_for(user_id: int) -> str:
    return f"user-{user_id}"


def upsert_document(
    user_id: int,
    document_id: int,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    vectors = [
        {
            "id": f"{document_id}#chunk-{chunk_id}",
            "values": embedding,
            "metadata": {
                "document_id": document_id,
                "chunk_id": chunk_id,
                "filename": filename,
                "text": chunk,
            },
        }
        for chunk_id, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    index = get_index()
    namespace = namespace_for(user_id)
    index.upsert(
        vectors=vectors,
        namespace=namespace,
        batch_size=BATCH_SIZE,
        show_progress=False,
    )


def delete_document(user_id: int, document_id: int) -> None:
    """Remove one document's vectors, leaving the user's other documents intact."""
    index = get_index()
    namespace = namespace_for(user_id)
    try:
        index.delete(
            filter={"document_id": {"$eq": document_id}},
            namespace=namespace,
        )
    except NotFoundException:
        # Namespace was never created (nothing ingested yet) — nothing to delete.
        pass
    except Exception:
        # Delete-by-metadata is rate limited to 5 rps per namespace; fall back to
        # listing the document's IDs by prefix and deleting those.
        ids: list[str] = []
        for page in index.list(prefix=f"{document_id}#", namespace=namespace):
            # Pinecone SDK releases have returned both a list of IDs and an
            # object containing vector records. Supporting either keeps the
            # fallback useful across serverless client versions.
            if isinstance(page, str):
                ids.append(page)
            elif isinstance(page, (list, tuple)):
                ids.extend(str(item) for item in page)
            else:
                ids.extend(str(getattr(item, "id", item)) for item in (getattr(page, "vectors", None) or []))
        for start in range(0, len(ids), BATCH_SIZE):
            index.delete(ids=ids[start:start + BATCH_SIZE], namespace=namespace)


def delete_all_for_user(user_id: int) -> None:
    try:
        get_index().delete(delete_all=True, namespace=namespace_for(user_id))
    except NotFoundException:
        pass


def search(
    user_id: int,
    query_embedding: list[float],
    k: int = TOP_K,
    document_id: int | None = None,
):
    query_filter = {"document_id": {"$eq": document_id}} if document_id else None
    try:
        result = get_index().query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True,
            namespace=namespace_for(user_id),
            filter=query_filter,
        )
    except NotFoundException:
        return []
    return result.matches or []
