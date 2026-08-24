# RAG Document Chat

A deployable, multi-user document question-answering app. Each account has private
conversation threads and private document vectors; PDFs, DOCX, TXT, and images are
indexed for grounded Gemini answers.

## What it does

- Email/password accounts secured with bcrypt and signed JWTs.
- ChatGPT-style conversation history: new chats, automatic titles, revisit, and delete.
- Upload PDFs, DOCX files, plain text (TXT), plus PNG, JPEG, and WebP images. Images are
  transcribed and described by Gemini vision before text embeddings are stored.
- Per-user Pinecone namespaces and per-document filters, so one account cannot search
  another account's documents.
- A Streamlit chat UI with document selection and collapsible citations.

## Local setup

Use Python 3.11+ and create a virtual environment. Install backend requirements, copy
`.env.example` to `.env`, then provide Gemini, Pinecone, and JWT values.

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

In a second terminal, install the small frontend dependency set and run Streamlit:

```powershell
venv\Scripts\python.exe -m pip install -r frontend/requirements.txt
venv\Scripts\python.exe -m streamlit run frontend/app.py
```

The API is documented locally at `http://127.0.0.1:8001/docs`; the UI defaults to that
same address. Set `API_BASE_URL` when the API is hosted elsewhere.

## Configuration

`DATABASE_URL` defaults to `sqlite:///./rag.db` for local work. In production, set it
to a durable Supabase PostgreSQL URL: Render free web-service storage is ephemeral.

For Supabase, use the **Session pooler** connection string from
**Project Settings → Database → Connection string → Session pooler**:

```
postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

The tables (`users`, `conversations`, `messages`, `documents`) are created
automatically on first startup via `Base.metadata.create_all`. If you prefer to
create them manually, run the app once against Supabase or use the SQL Editor.

Required production variables are `GEMINI_API_KEY`, `PINECONE_API_KEY`,
`PINECONE_INDEX_HOST`, `JWT_SECRET`, `DATABASE_URL`, and `CORS_ORIGINS`. See
`.env.example` for optional model, retrieval, and upload settings. Generate a unique,
long `JWT_SECRET`; the API intentionally refuses to start without one.

## Deployment

### API — FastAPI Cloud

Deploy the API to [FastAPI Cloud](https://fastapi.cloud):

1. Push this repository to GitHub.
2. Log in to [fastapi.cloud](https://fastapi.cloud) and create a new project.
3. Connect your GitHub account and select this repository.
4. Set the required environment variables in the dashboard:
   - `GEMINI_API_KEY`
   - `PINECONE_API_KEY`
   - `PINECONE_INDEX_HOST`
   - `JWT_SECRET`
   - `DATABASE_URL` (your Supabase Session pooler URL)
   - `CORS_ORIGINS` (your Streamlit app URL, e.g. `https://your-app.streamlit.app`)
5. Deploy. The app entry point is `app.main:app` (see `fastapi-cloud.yaml`).

### Frontend — Streamlit Community Cloud

Deploy `frontend/app.py` on Streamlit Community Cloud. Add this Streamlit secret:

```toml
API_BASE_URL = "https://your-fastapi-cloud-app.fastapi.app"
```

The frontend uses a 120-second API timeout and presents a friendly retry message.

## Tests

The API tests run without Gemini or Pinecone credentials by replacing those external
boundaries with an in-memory fake:

```powershell
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest -q
```
