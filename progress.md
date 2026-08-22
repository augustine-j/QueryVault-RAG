\# Multi-user chatbot RAG: auth, chat history, image ingest, deploy



\## Context



The project is a single-user, single-document RAG API (FastAPI + Gemini + Pinecone) with a

Streamlit UI that is half chat, half analytics dashboard. Everything is global: one Pinecone

namespace `"current-document"` that every upload wipes (\[app/vector\_store.py:17](app/vector\_store.py:17)),

one flat `query\_logs` table with no owner, and no login.



The goal is to turn it into a deployable multi-user document chatbot:



\- drop the analytics dashboard and its backend code entirely

\- add email/password auth, with users in SQL

\- persist chat as ChatGPT-style conversation threads a user can revisit

\- accept images as well as PDFs, extracting their content via Gemini vision

\- redesign the Streamlit UI around the chat/thread model

\- run the API on Render free tier and the UI on Streamlit Community Cloud



Two problems block a plain "add auth" change and are handled below:

Render's free filesystem is ephemeral, so a SQLite file there is erased on every redeploy and

idle spin-down (\[Render docs](https://render.com/docs/disks): "without a persistent disk, any

changes you make to a service's local files are lost every time the service redeploys or

restarts"); and the current global namespace means one user's upload would delete every other

user's document.



\## Decisions (confirmed with user)



| Area | Decision |

|---|---|

| Database | SQLAlchemy driven by a `DATABASE\_URL` env var, default `sqlite:///./rag.db`. SQLite locally; a free Neon/Supabase Postgres URL on Render. No code differences. |

| History | Conversation threads: sidebar list, auto-titled, click to reload, new chat + delete. |

| Documents | Pinecone namespace per user + `document\_id` metadata; multiple docs per user with a picker. |

| Analytics | Deleted: `app/routers/analytics.py`, `get\_analytics()`, the `QueryLog` model. |



\## Backend



\### New: `app/config.py`



Central `os.getenv` reads (currently scattered across modules, and `os.environ\[...]` at import

time in \[app/rag.py:6](app/rag.py:6) / \[app/embeddings.py:7](app/embeddings.py:7) / \[app/vector\_store.py:11](app/vector\_store.py:11),

which crashes the whole app on a missing key). Keys: `DATABASE\_URL`, `GEMINI\_API\_KEY`,

`GEMINI\_MODEL`, `PINECONE\_API\_KEY`, `PINECONE\_INDEX\_HOST`, `JWT\_SECRET`,

`JWT\_EXPIRE\_MINUTES` (default 7 days), `CORS\_ORIGINS`.



\### New: `app/security.py`



\- `hash\_password` / `verify\_password` using the `bcrypt` package directly — not `passlib`, whose

&#x20; 1.7.4 release breaks against bcrypt 4.x. Reject passwords over bcrypt's 72-byte limit at the

&#x20; schema layer instead of silently truncating.

\- `create\_access\_token(user\_id)` / `decode\_access\_token(token)` with `PyJWT`, HS256.



\### New models



`app/models/user.py` — `User`: `id`, `email` (unique, indexed), `hashed\_password`, `full\_name`,

`created\_at`.



`app/models/chat.py`

\- `Conversation`: `id`, `user\_id` FK, `title`, `created\_at`, `updated\_at`.

\- `Message`: `id`, `conversation\_id` FK, `role` (`user`/`assistant`), `content`,

&#x20; `sources` (JSON text, null for user turns), `response\_time`, `created\_at`.



`app/models/document.py` — `Document`: `id`, `user\_id` FK, `filename`, `kind` (`pdf`/`image`),

`chunk\_count`, `created\_at`.



Cascade deletes on the relationships so removing a conversation or user cleans up children.

`Base.metadata.create\_all` in \[app/main.py:9](app/main.py:9) already handles table creation; no Alembic.



\### Schemas: `app/models/schemas.py`



Replaces \[app/models/questions.py](app/models/questions.py). Keeps `SourceItem`, adds

`UserCreate` / `UserLogin` / `UserOut` / `TokenOut`, `AskRequest` (`question`,

`conversation\_id?`, `document\_id?`), `AskResponse` (`conversation\_id`, `answer`, `sources`,

`response\_time`), `ConversationOut`, `MessageOut`, `DocumentOut`.



\### Extraction: `app/extraction.py`



\- `extract\_pdf\_text(data: bytes) -> str` — the `PdfReader` logic lifted out of

&#x20; \[app/rag\_service.py:13](app/rag\_service.py:13), reading from `io.BytesIO` rather than a path.

\- `extract\_image\_text(data: bytes, mime\_type: str) -> str` — one Gemini vision call reusing the

&#x20; `client` and `MODEL` already configured for chat, via

&#x20; `types.Part.from\_bytes(data=..., mime\_type=...)` plus a prompt that asks for a verbatim

&#x20; transcription of all visible text \*and\* a description of charts/tables/diagrams, so screenshots

&#x20; and photos of documents both index usefully. Gemini's embedding model is text-only, so this

&#x20; image→text step is what makes images searchable at all.



Uploads are handled in memory. Today \[app/routers/ingest.py:25](app/routers/ingest.py:25) writes to

`data/` and then calls `rag.ingest\_pdf` \*inside\* the still-open `with open(...)` block, so the

file may not be flushed when it is re-read — that bug disappears along with the disk write, which

would be pointless on Render's ephemeral disk anyway.



\### Vector store: `app/vector\_store.py`



\- `\_namespace(user\_id) -> f"user-{user\_id}"` — per-user isolation, so

&#x20; \[app/vector\_store.py:17](app/vector\_store.py:17)'s `delete\_all` no longer nukes other users.

\- `upsert\_document(user\_id, document\_id, chunks, embeddings)` — IDs `f"{document\_id}#chunk-{i}"`

&#x20; (Pinecone's recommended prefix convention) and metadata `{document\_id, chunk\_id, text,

&#x20; filename}`. Keeps the existing 100-vector batching.

\- `delete\_document(user\_id, document\_id)` — `index.delete(filter={"document\_id": {"$eq": ...}},

&#x20; namespace=ns)`. Delete-by-metadata is supported and documented for serverless indexes; the `#`

&#x20; ID prefix gives an `index.list(prefix=...)` fallback if that ever rate-limits (5 rps/namespace).

\- `delete\_namespace(user\_id)` — used when a user account is removed.

\- `search(user\_id, query\_embedding, k=5, document\_id=None)` — namespace-scoped, with an optional

&#x20; `document\_id` metadata filter when the user has a specific document selected.



\### RAG service: `app/rag\_service.py`



\- `ingest(user\_id, document\_id, filename, data, mime\_type)` — dispatches to the right extractor,

&#x20; reuses \[`chunk\_text`](app/chunker.py:1) and \[`create\_embeddings`](app/embeddings.py:25)

&#x20; unchanged, calls `upsert\_document`, returns the chunk count. Raises a clear error when

&#x20; extraction yields no text (scanned PDF with no text layer, blank image).

\- `ask(user\_id, question, document\_id=None, history=None)` — same shape as

&#x20; \[app/rag\_service.py:22](app/rag\_service.py:22), plus two conversation-aware touches:

&#x20; - \*\*Retrieval:\*\* when the thread has prior turns, embed `previous\_question + " " + question` so

&#x20;   follow-ups like "what about the second one?" still retrieve something relevant. Cheap

&#x20;   heuristic, no extra LLM call.

&#x20; - \*\*Generation:\*\* \[`ask\_llm`](app/rag.py:9) gains an optional `history` argument and renders the

&#x20;   last \~6 messages above the context block, so the model can resolve pronouns and follow-ups.

&#x20;   The "I could not find the answer in the document." instruction stays as-is.



\### Auth dependency: `app/dependencies.py`



Add `get\_current\_user(credentials = Depends(HTTPBearer()), db = Depends(get\_db))` — decode the

JWT, load the `User`, raise 401 on bad/expired token or missing user. The existing module-level

`rag = RAGService()` and `get\_db` stay.



\### Routers



\*\*`app/routers/auth.py` (new)\*\*

\- `POST /auth/register` → 201, creates the user, returns a token (409 on duplicate email).

\- `POST /auth/login` → JSON body `{email, password}` (not OAuth2 form — the Streamlit client

&#x20; posts JSON), returns token + user. 401 on bad credentials.

\- `GET /auth/me` → current user; the frontend uses it to validate a cached token.



\*\*`app/routers/chat.py` (new)\*\* — all `Depends(get\_current\_user)` and all scoped by `user\_id` so

one user can never read another's thread (404, not 403, on someone else's id).

\- `GET /conversations`, `POST /conversations`, `GET /conversations/{id}` (with messages),

&#x20; `DELETE /conversations/{id}`, `PATCH /conversations/{id}` for rename.



\*\*`app/routers/documents.py` (new)\*\* — `GET /documents`, `DELETE /documents/{id}`

(vectors + row).



\*\*`app/routers/ingest.py` (rewrite)\*\* — authenticated; accepts `application/pdf` and

`image/png|jpeg|webp` (replacing the `.pdf`-only check at

\[app/routers/ingest.py:18](app/routers/ingest.py:18)); validates by extension \*and\* content type,

caps size (\~10 MB); creates the `Document` row, ingests, returns `DocumentOut`.



\*\*`app/routers/ask.py` (rewrite)\*\* — authenticated. Creates the conversation when

`conversation\_id` is absent, auto-titling from the first \~60 chars of the question; loads recent

history; calls `rag.ask`; persists the user message and the assistant message (with `sources` and

`response\_time`); bumps `conversation.updated\_at`. `save\_query` in

\[app/store\_getQuery.py](app/store\_getQuery.py) is replaced by chat-message persistence in a new

`app/crud.py`; the file and its `get\_analytics` are deleted.



\*\*`app/main.py`\*\* — drop the analytics import/include, wire auth/chat/documents, add

`CORSMiddleware` from `CORS\_ORIGINS`, and keep `GET /` as the Render health check.



\### Deleted



`app/routers/analytics.py`, `app/store\_getQuery.py`, `app/models/query\_log.py`,

`app/models/questions.py` (superseded by `schemas.py`).



\## Frontend



\[frontend/app.py](frontend/app.py) is currently one 124-line script with the dashboard interleaved

into the chat flow, and it re-fetches `/analytics` on every rerun. It gets split:



\- \*\*`frontend/api.py`\*\* — thin `requests` wrapper: `BASE\_URL` from `st.secrets`/env with a

&#x20; localhost fallback, `Authorization: Bearer` header injected from session state, a single

&#x20; `\_request` helper that returns `(ok, payload)` so views never crash on a non-200, and a

&#x20; generous timeout (see the Render cold-start note below).

\- \*\*`frontend/styles.py`\*\* — one `inject\_css()` with the custom CSS.

\- \*\*`frontend/auth\_view.py`\*\* — centred card, `Sign in` / `Create account` tabs, inline field

&#x20; validation, and `st.form` so Enter submits.

\- \*\*`frontend/chat\_view.py`\*\* — sidebar + thread.

\- \*\*`frontend/app.py`\*\* — `set\_page\_config`, CSS injection, session-state bootstrap, and the

&#x20; branch between auth view and chat view.



\### Layout



```

┌── sidebar ───────────────┬── main ────────────────────────────┐

│  ● RAG Chat              │   Conversation title    \[doc chip] │

│  \[ + New chat ]          │                                    │

│                          │   ┌ user bubble (right-ish) ─────┐ │

│  RECENT                   │   └──────────────────────────────┘ │

│  › AWS liability terms   │   ┌ assistant bubble ────────────┐ │

│  › Module 1 summary   🗑  │   │ answer markdown              │ │

│  › Invoice total         │   │ ▸ 3 sources                  │ │

│                          │   └──────────────────────────────┘ │

│  DOCUMENTS               │                                    │

│  \[ drop pdf / image ]    │   \[ Ask about your documents… ]    │

│  ▣ module1.pdf           │                                    │

│  ▣ s1 result.pdf      🗑  │                                    │

│  ◻ All documents         │                                    │

│  ─────────────────────    │                                    │

│  AJ  augustine  \[logout] │                                    │

└──────────────────────────┴────────────────────────────────────┘

```



\### Visual direction



Not a generic Streamlit page: a dark, low-chroma neutral shell (`#0f1115` app, `#15181e`

sidebar) with a single warm accent for the primary action and the active thread, set in

`.streamlit/config.toml` so widgets inherit it rather than fighting the CSS. Asymmetric bubbles —

user turns a filled accent-tinted surface, assistant turns transparent with a hairline left

border — so the thread reads at a glance without avatars shouting. Sources collapse into a

quiet `▸ 3 sources` disclosure under the answer instead of the current always-open

`st.subheader("Sources")` + expander stack. Uploaded images render as a thumbnail in their

document row. Tight vertical rhythm: the default Streamlit block padding is cut so the composer

sits at the bottom of the viewport like a real chat client.



\### Behaviour



\- Session state: `token`, `user`, `conversation\_id`, `messages`, `document\_id`, `documents`.

\- Optimistic send: append the user bubble and `st.spinner` before the `/ask` call, then persist

&#x20; the returned assistant message — the current code renders the answer \*outside\* the

&#x20; `st.chat\_message("assistant")` block (\[frontend/app.py:57](frontend/app.py:57)), so it escapes

&#x20; the bubble; the rewrite fixes that.

\- Selecting a thread fetches `GET /conversations/{id}` and replays it.

\- Conversation list and documents are fetched once per rerun-cycle and cached in session state,

&#x20; invalidated on send/upload/delete.

\- Deleting a thread asks for confirmation inline (a second click), never a silent destructive

&#x20; action.

\- \*\*Caveat:\*\* the token lives in `st.session\_state`, which Streamlit clears on a browser refresh,

&#x20; so a hard refresh means re-login. Acceptable for this app; if you want refresh-persistent

&#x20; sessions later, `extra-streamlit-components`' `CookieManager` is the usual add-on.



\## Dependencies



\[requirements.txt](requirements.txt) is currently wrong for this codebase in both directions: it

pins `faiss-cpu`, `sentence-transformers`, `torch`, and `transformers` — leftovers from the

pre-Gemini version, \~2.5 GB of wheels that will exhaust a Render free build — while omitting

`google-genai`, `pinecone`, and `python-dotenv`, which the code actually imports. It gets replaced

with a hand-written backend list pinned to what is already in `venv`:



```

fastapi==0.137.1        pinecone==9.1.0         PyJWT==2.10.1

uvicorn\[standard]       google-genai==2.19.0    bcrypt==5.0.0

SQLAlchemy==2.0.51      pypdf==6.13.2           psycopg2-binary==2.9.10

pydantic==2.13.4        python-dotenv==1.2.3    email-validator

python-multipart==0.0.32

```



`frontend/requirements.txt` gets just `streamlit==1.58.0` and `requests==2.34.2`.

`requirements-dev.txt` adds `pytest` and `httpx` (already installed) for the test suite.



\## Deployment



\### Backend — Render (free web service)



\- Build `pip install -r requirements.txt`; start

&#x20; `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (Render injects `$PORT`; the hardcoded

&#x20; 8001 in the current frontend is local-only).

\- Health check path `/`, which \[app/main.py:19](app/main.py:19) already serves.

\- Env vars: the four existing keys plus `JWT\_SECRET`, `DATABASE\_URL`, `CORS\_ORIGINS`.

\- A committed `render.yaml` blueprint so the service is reproducible, with `sync: false` on the

&#x20; secrets so they are entered in the dashboard, never in git.

\- \*\*Cold start:\*\* free instances spin down after \~15 minutes idle and take \~50 s to wake. The API

&#x20; client therefore uses a 120 s timeout and the login screen fires a background `GET /` warm-up

&#x20; ping, with a "waking the server up…" message instead of a raw timeout traceback.

\- \*\*Free Postgres caveat:\*\* Render's own free Postgres expires 30 days after creation, so point

&#x20; `DATABASE\_URL` at Neon or Supabase instead for a database that outlives the demo.



\### Frontend — Streamlit Community Cloud



Entrypoint `frontend/app.py`. Community Cloud accepts a requirements file "either in the root of

your repository or in the same directory as your app's entrypoint file", so

`frontend/requirements.txt` is picked up; if it resolves the root file instead the app still runs,

since `streamlit` and `requests` are pre-installed there. `BASE\_URL` goes in the app's

Secrets as `API\_BASE\_URL = "https://<service>.onrender.com"`, read via `st.secrets`.



\### Security notes



\- `JWT\_SECRET` must be a long random value; the app raises at startup rather than falling back to

&#x20; a built-in default, so a deploy can't silently ship a guessable signing key.

\- Passwords: bcrypt, min 8 chars, max 72 bytes (bcrypt's hard limit) rejected at the schema layer.

\- Every chat/document/ask route is behind `get\_current\_user` and filtered by `user\_id`; there is

&#x20; no unauthenticated data path. Known gap, called out rather than hidden: no rate limiting on

&#x20; `/auth/login`, so the public deploy is brute-forceable — fine for a demo, worth adding

&#x20; `slowapi` if this goes further.

\- `.env` and `\*.db` are already in \[.gitignore](.gitignore); a `.env.example` documents the keys

&#x20; without values.



\## Verification



\### Automated — `tests/test\_api.py` (new, pytest + `TestClient`)



Runs offline: `dependency\_overrides` swaps `get\_db` for a temp-file SQLite session, and the Gemini

and Pinecone boundaries are monkeypatched (`embeddings.embed` → a fixed vector,

`vector\_store.index` → a fake, `rag.ask\_llm` → a canned answer), so no API keys or network are

needed. Cases:



1\. register → 201 + token; same email again → 409.

2\. login with wrong password → 401; any chat route without a token → 401/403.

3\. `POST /ask` with no `conversation\_id` creates a thread, auto-titles it, and stores exactly two

&#x20;  messages with the right roles.

4\. `POST /ask` with the thread id appends to it rather than creating a second one.

5\. User B gets 404 on User A's conversation id, and `GET /conversations` never crosses users.

6\. `/ingest` accepts a 1-page PDF and a small PNG, rejects `.txt` with 400.

7\. `DELETE /documents/{id}` removes the row and calls the vector delete with the right namespace.



Run: `venv/Scripts/python.exe -m pytest -q`



\### Manual — local end to end



```bash

venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8001

```



```bash

venv/Scripts/python.exe -m streamlit run frontend/app.py

```



Then, in the browser: create an account → confirm the sidebar is empty → upload

`data/module1.pdf` and ask something answerable from it → check the answer lands inside the

assistant bubble with a collapsed sources disclosure → ask a follow-up that relies on the previous

turn ("and what about the second one?") and confirm the history-aware retrieval still answers →

upload a screenshot/photo containing text and ask about its contents → start a new chat, then

click back into the first thread and confirm the full transcript replays → log out, register a

second account, and confirm it sees neither the first account's threads nor its documents (this is

the regression that the old shared `"current-document"` namespace would have caused) → confirm no

analytics UI or `/analytics` route remains (`curl -i localhost:8001/analytics` → 404).



Check `/docs` for the final route list, and re-run the flow once against the deployed Render URL

by pointing `API\_BASE\_URL` at it, to confirm the cold-start path behaves.



\## Files



| Action | Path |

|---|---|

| new | `app/config.py`, `app/security.py`, `app/crud.py`, `app/extraction.py`, `app/models/user.py`, `app/models/chat.py`, `app/models/document.py`, `app/models/schemas.py`, `app/routers/auth.py`, `app/routers/chat.py`, `app/routers/documents.py` |

| rewrite | \[app/main.py](app/main.py), \[app/database.py](app/database.py), \[app/dependencies.py](app/dependencies.py), \[app/vector\_store.py](app/vector\_store.py), \[app/rag\_service.py](app/rag\_service.py), \[app/routers/ask.py](app/routers/ask.py), \[app/routers/ingest.py](app/routers/ingest.py), \[frontend/app.py](frontend/app.py), \[requirements.txt](requirements.txt), \[readme.md](readme.md) |

| small edit | \[app/rag.py](app/rag.py) (optional `history` arg), \[app/embeddings.py](app/embeddings.py) (config import) |

| unchanged | \[app/chunker.py](app/chunker.py) |

| new frontend | `frontend/api.py`, `frontend/styles.py`, `frontend/auth\_view.py`, `frontend/chat\_view.py`, `frontend/requirements.txt`, `.streamlit/config.toml` |

| deleted | `app/routers/analytics.py`, `app/store\_getQuery.py`, `app/models/query\_log.py`, `app/models/questions.py` |

| infra | `render.yaml`, `.env.example`, `requirements-dev.txt`, `tests/` |



The \[readme.md](readme.md) is stale in a way worth fixing while here: it documents FAISS,

Ollama `llama3.2:3b`, and `all-MiniLM-L6-v2`, none of which the code has used since the Gemini +

Pinecone rewrite. It gets updated to the real stack, the new auth/chat/image features, and the two

deployment targets.

