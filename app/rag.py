from app.config import GEMINI_MODEL
from app.gemini_client import get_client

NOT_FOUND_MESSAGE = "I could not find the answer in the document."

SYSTEM_RULES = f"""You are QueryVault, a helpful assistant that answers questions about the
user's uploaded documents.

Rules:
1. If the Context below contains the information needed to answer, base your answer ONLY on
   it. Be faithful to the source: never invent facts, numbers, or quotes that are not in the
   context. When relevant, mention which document (filename) the information came from.
2. If the Context does not fully cover the question, you may add information from your own
   general knowledge, but you MUST clearly separate it: state that it is general knowledge,
   not from the user's documents. Append a line such as:
   "_Note: this part comes from my general knowledge and was not found in your documents._"
3. Use the Conversation so far only to understand what the user is referring to (follow-ups,
   pronouns). Never treat past conversation text as a source of facts about the documents.
4. Write concise, well-structured Markdown answers. Use bullets or headings for multi-part
   answers.
5. If you cannot answer from either source, reply exactly: "{NOT_FOUND_MESSAGE}"
"""


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
