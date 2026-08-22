from app.chunker import chunk_text
from app.config import CHUNK_OVERLAP, CHUNK_SIZE, TOP_K
from app.embeddings import create_embeddings, create_query_embedding
from app.extraction import extract_text
from app.rag import NOT_FOUND_MESSAGE, ask_llm
from app.vector_store import delete_document, search, upsert_document

NO_DOCUMENT_MESSAGE = (
    "You have not uploaded any documents yet. Add a PDF or an image from the sidebar "
    "and I will answer questions about it."
)


class RAGService:
    def ingest(
        self,
        user_id: int,
        document_id: int,
        filename: str,
        data: bytes,
        content_type: str | None,
    ) -> tuple[int, str]:
        """Extract, chunk, embed and store one file. Returns (chunk_count, kind)."""
        text, kind = extract_text(data, filename, content_type)
        chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        embeddings = create_embeddings(chunks)
        upsert_document(user_id, document_id, filename, chunks, embeddings)
        return len(chunks), kind

    def remove(self, user_id: int, document_id: int) -> None:
        delete_document(user_id, document_id)

    def ask(
        self,
        user_id: int,
        question: str,
        document_id: int | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        matches = search(
            user_id,
            create_query_embedding(self._retrieval_query(question, history)),
            k=TOP_K,
            document_id=document_id,
        )

        if not matches:
            return {"answer": NO_DOCUMENT_MESSAGE, "sources": []}

        sources = [
            {
                "chunk_id": match.metadata.get("chunk_id", 0),
                "text": match.metadata.get("text", ""),
                "filename": match.metadata.get("filename"),
                "score": getattr(match, "score", None),
            }
            for match in matches
        ]

        context = "\n\n".join(source["text"] for source in sources)
        answer = ask_llm(question, context, history=history)

        return {"answer": answer, "sources": sources}

    @staticmethod
    def _retrieval_query(question: str, history: list[dict] | None) -> str:
        """Prepend the previous question so follow-ups still retrieve something.

        "and what about the second one?" carries almost no searchable signal on its
        own; pairing it with the preceding question recovers the topic without
        spending an extra LLM call on query rewriting.
        """
        if not history:
            return question
        previous = next(
            (
                turn["content"]
                for turn in reversed(history)
                if turn["role"] == "user" and turn["content"] != question
            ),
            None,
        )
        return f"{previous} {question}" if previous else question


__all__ = ["RAGService", "NOT_FOUND_MESSAGE", "NO_DOCUMENT_MESSAGE"]
