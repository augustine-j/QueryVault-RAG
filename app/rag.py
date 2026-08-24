from google.genai import types

from app.config import GEMINI_MODEL, SEARCH_FALLBACK
from app.gemini_client import get_client

NOT_FOUND_MESSAGE = "I could not find the answer in the document."

SYSTEM_RULES = f"""You are QueryVault, a helpful assistant that answers questions about the
user's uploaded documents.

Rules:
1. If the Context below contains the information needed to answer, base your answer ONLY on
   it. Be faithful to the source: never invent facts, numbers, or quotes that are not in the
   context. When relevant, mention which document (filename) the information came from.
2. If the Context does NOT contain the answer, do NOT use the "could not find" message.
   Instead, answer directly from your own general knowledge, and append this note at the end
   of your answer:
   "_Note: this part comes from my general knowledge and was not found in your documents._"
3. Use the Conversation so far only to understand what the user is referring to (follow-ups,
   pronouns). Never treat past conversation text as a source of facts about the documents.
4. Write concise, well-structured Markdown answers. Use bullets or headings for multi-part
   answers.
5. Reply exactly "{NOT_FOUND_MESSAGE}" ONLY when BOTH are true: the Context lacks the answer
   AND you genuinely do not know the answer yourself. Never mix this message with any other
   content.
"""

SEARCH_RULES = """You are QueryVault's web-research mode. The user asked a question that their
uploaded documents could not answer, so you may consult Google Search results.

Rules:
1. Answer using up-to-date information found via Google Search. Be accurate and concise.
2. Make clear that this answer comes from live web research, not from the user's uploaded
   documents. Append a line such as:
   "_Note: this answer comes from a web search, not from your uploaded documents._"
3. If the search results do not settle the question, say so honestly rather than guessing.
4. Write concise, well-structured Markdown answers.
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


def _generate(prompt: str, tools: list | None = None) -> str:
    """Call Gemini once and return its text (empty string when unset)."""
    config = types.GenerateContentConfig(tools=tools) if tools else None
    response = get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )
    return response.text or ""


def ask_llm_with_search(question: str, history: list[dict] | None = None) -> str:
    """Answer using Google Search grounding; used when documents lack the answer."""
    prompt = (
        f"{SEARCH_RULES}\n\n"
        f"{_render_history(history)}"
        f"Question: {question}\nAnswer:"
    )
    try:
        text = _generate(
            prompt, tools=[types.Tool(google_search=types.GoogleSearch())]
        ).strip()
    except Exception:
        # Search grounding is best-effort; degrade to the plain not-found reply.
        return NOT_FOUND_MESSAGE
    return text or NOT_FOUND_MESSAGE


def ask_llm(question: str, context: str, history: list[dict] | None = None) -> str:
    prompt = (
        f"{SYSTEM_RULES}\n\n"
        f"{_render_history(history)}"
        f"Context:\n{context}\n\n"
        f"Question: {question}\nAnswer:"
    )

    try:
        answer = _generate(prompt).strip() or NOT_FOUND_MESSAGE
    except Exception as error:
        raise RuntimeError(f"Gemini request failed: {error}") from error

    # Documents had no answer: retry once with Google Search grounding so
    # recent real-world questions still get a useful, clearly labeled reply.
    if answer == NOT_FOUND_MESSAGE and SEARCH_FALLBACK:
        web_answer = ask_llm_with_search(question, history)
        if web_answer != NOT_FOUND_MESSAGE:
            return web_answer
    return answer
