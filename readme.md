# RAG Q&A System

## Overview

This project implements a Retrieval-Augmented Generation (RAG) system for answering questions from the AWS Customer Agreement PDF. The application combines semantic search, a local LLM, SQL-based usage logging, and a web dashboard.

The system allows users to:

* Upload and process a PDF document
* Ask questions about the document
* View generated answers with supporting source chunks
* Analyze system usage through an analytics dashboard

---

## Technology Stack

### Backend

* FastAPI
* Python

### Retrieval Pipeline

* Sentence Transformers - all-MiniLM-L6-v2
* FAISS

### LLM

* Ollama (Local Model) - llama3.2:3b

### Database

* SQLite
* SQLAlchemy

### Frontend

* Streamlit

---

## Project Structure

```text
RAG-QA-SYSTEM
│
├── app
│   ├── models
│   ├── routers
│   ├── chunker.py
│   ├── database.py
│   ├── dependecies.py
│   ├── embeddings.py
│   ├── main.py
│   ├── rag_service.py
│   ├── rag.py
│   ├── store_getQuery.py
│   └── vector_store.py
│
├── frontend
│   └── app.py
│
├── requirements.txt
└── README.md

```


## Architecture Overview

PDF Document

↓

Text Extraction using PdfReader

↓

Chunking

↓

Embedding Generation using SentenceTransformer(all-MiniLM-L6-v2)

↓

FAISS Vector Store

-------------------------------------------------------------------
User Question

↓

Question Embedding

↓

FAISS Similarity Search

↓

Top-K Retrieval

↓

Prompt Construction

↓

Ollama LLM

↓

Generated Answer + Sources

↓

SQLite Logging

↓

Analytics Endpoint

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/augustine-j/RAG-based-Document-Q-A-System-with-Analytics-Dashboard-.git
cd RAG-QA-SYSTEM
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Install And Run Ollama

Download and install Ollama.

Pull the model llama3.2:3b :

```bash
ollama pull llama3.2:3b
```
Run the model

```bash
ollama run llama3.2:3b
```


### 6. Run FastAPI Backend

```bash
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

### 7. Run Streamlit Frontend

Open another terminal:

```bash
streamlit run frontend/app.py
```

Frontend URL:

```text
http://localhost:8501/
```

---

## API Endpoints

### POST /ingest

Processes and indexes the uploaded PDF document.

### POST /ask

Accepts a user question and returns:

* Generated Answer
* Source Chunks

### GET /analytics

Returns:

* Most Frequently Asked Questions
* Queries With No Answer Found
* Average Response Latency
* total queries
* successful_answers
* failed_answers
* sucess_rate


---

## Design Decisions

### Chunking Strategy

* Chunk Size: 1000 characters
* Overlap: 100 characters

This configuration was selected to preserve context while maintaining retrieval efficiency.

### Embedding Model

* all-MiniLM-L6-v2

Chosen because it is lightweight, efficient, and produces high-quality semantic embeddings.

### Vector Store

* FAISS

Chosen for fast local similarity search without requiring external infrastructure.

### LLM Choice

* Ollama Local Model llama3.2:3b

Chosen to avoid external API costs and enable completely local execution.

### Retrieval Strategy

* Top-K = 5

The five most relevant chunks are retrieved and supplied to the language model as context.

---

## Edge Cases Handled

* Empty Questions
* No Document Ingested
* Invalid File Uploads
* Out-of-Scope Questions

---

## References

The following resources are used for beuilding this project

# FastAPI
* https://fastapi.tiangolo.com/
* https://fastapi.tiangolo.com/tutorial/request-files/
* https://medium.com/@gopinath.v2507/python-fastapi-how-to-connect-fastapi-to-database-203be23c81e9

# Streamlit
* https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps
* https://docs.kanaries.net/topics/Streamlit/streamlit-upload-file
* https://medium.com/@obaff/building-a-website-with-python-fastapi-and-streamlit-418f48c41af2

# LLM Model
* https://ollama.com/
# sentence transformer for embeddings 
* https://www.sbert.net/

# FAISS
* https://thepythoncode.com/article/semantic-search-engine-faiss-python

# source file
* AWS Customer Agreement

# AI Assistance

AI-assisted development  were used alongside official documentation, tutorials, and articles during the project for:

* implementation  guidance
* Understanding framework concepts
* Architecture discussions
* Code review and troubleshooting




