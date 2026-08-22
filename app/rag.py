from app.config import GEMINI_MODEL
from app.gemini_client import get_client

NOT_FOUND_MESSAGE = "I could not find the answer in the document."

SYSTEM_RULES = f"""You are a document assistant. Answer the question using only the
context extracted from the user's uploaded documents. If the answer is not in the
context, reply exactly: "{NOT_FOUND_MESSAGE}"
Use the conversation so far only to understand what the user is referring to, never as
a source of facts."""


def _render_history(history: list[dict] | None) -> str:
    """Render recent turns so the model can resolve follow-ups and pronouns."""
    if not history:
        return ""
    lines = [
        f"{'User' if turn['role'] == 'user' else 'Assistant'}: {turn['content']}"
        for turn in history
    ]
    return "Conversation so far:\n" + "\n".join(lines) + "\n\n"


def ask_llm(question: str, context: str, history: list[dict] | None = None) -> str:
    prompt = (
        f"{SYSTEM_RULES}\n\n"
        f"{_render_history(history)}"
        f"Context:\n{context}\n\n"
        f"Question: {question}\nAnswer:"
    )

    try:
        response = get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text or NOT_FOUND_MESSAGE
    except Exception as error:
        raise RuntimeError(f"Gemini request failed: {error}") from error
