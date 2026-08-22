"""Authenticated conversation and document UI."""

from html import escape

import streamlit as st

from api import ask, conversation, conversations, delete_conversation, delete_document, documents, upload_document
from session import clear_token


def _detail(payload: object) -> str:
    return payload.get("detail", "Request failed.") if isinstance(payload, dict) else "Request failed."


def _refresh_collections() -> None:
    ok, payload = conversations()
    st.session_state.conversations = payload if ok else []
    ok, payload = documents()
    st.session_state.documents = payload if ok else []


def _select_conversation(conversation_id: int) -> None:
    ok, payload = conversation(conversation_id)
    if not ok:
        st.error(_detail(payload))
        return
    st.session_state.conversation_id = payload["id"]
    st.session_state.messages = payload["messages"]
    st.session_state.conversation_title = payload["title"]
    st.rerun()


def _new_chat() -> None:
    st.session_state.conversation_id = None
    st.session_state.conversation_title = "New chat"
    st.session_state.messages = []
    st.rerun()


def _render_sidebar(cookie_manager) -> None:
    with st.sidebar:
        st.markdown('<div class="app-brand">● RAG Chat</div>', unsafe_allow_html=True)
        if st.button("+ New chat", use_container_width=True):
            _new_chat()

        st.markdown('<div class="section-label">RECENT</div>', unsafe_allow_html=True)
        for item in st.session_state.conversations:
            cols = st.columns([5, 1])
            if cols[0].button(item["title"], key=f"open-{item['id']}", use_container_width=True):
                _select_conversation(item["id"])
            key = f"confirm-thread-{item['id']}"
            if st.session_state.get(key):
                if cols[1].button("Yes", key=f"delete-thread-{item['id']}"):
                    ok, payload = delete_conversation(item["id"])
                    if not ok:
                        st.error(_detail(payload))
                    else:
                        if st.session_state.conversation_id == item["id"]:
                            st.session_state.conversation_id = None
                            st.session_state.messages = []
                        st.session_state.pop(key, None)
                        _refresh_collections()
                        st.rerun()
            elif cols[1].button("×", key=f"confirm-delete-thread-{item['id']}"):
                st.session_state[key] = True
                st.rerun()

        st.markdown('<div class="section-label">DOCUMENTS</div>', unsafe_allow_html=True)
        upload = st.file_uploader("Add PDF or image", type=["pdf", "png", "jpg", "jpeg", "webp"], label_visibility="collapsed")
        if upload is not None and st.button("Upload document", use_container_width=True):
            upload_bytes = upload.getvalue()
            with st.spinner("Reading and indexing document…"):
                ok, payload = upload_document(upload.name, upload_bytes, upload.type or "application/octet-stream")
            if ok:
                if payload["kind"] == "image":
                    st.session_state.setdefault("document_thumbnails", {})[payload["id"]] = upload_bytes
                st.success(f"Added {payload['filename']} ({payload['chunk_count']} chunks).")
                _refresh_collections()
                st.rerun()
            else:
                st.error(_detail(payload))

        docs = st.session_state.documents
        choices = [None] + [item["id"] for item in docs]
        labels = {None: "All documents", **{item["id"]: f"{item['filename']} ({item['kind']})" for item in docs}}
        current = st.session_state.get("document_id")
        index = choices.index(current) if current in choices else 0
        selected = st.selectbox("Search in", choices, index=index, format_func=labels.get)
        st.session_state.document_id = selected
        for item in docs:
            cols = st.columns([5, 1])
            thumbnail = st.session_state.get("document_thumbnails", {}).get(item["id"])
            if thumbnail:
                cols[0].image(thumbnail, width=44)
            cols[0].caption(f"{'▧' if item['kind'] == 'image' else '▣'} {item['filename']}")
            if cols[1].button("×", key=f"delete-document-{item['id']}"):
                ok, payload = delete_document(item["id"])
                if ok:
                    if st.session_state.document_id == item["id"]:
                        st.session_state.document_id = None
                    _refresh_collections()
                    st.rerun()
                else:
                    st.error(_detail(payload))

        st.divider()
        user = st.session_state.user
        st.caption(user.get("full_name") or user["email"])
        if st.button("Log out", use_container_width=True):
            clear_token(cookie_manager)
            for key in ("token", "user", "conversation_id", "conversation_title", "messages", "documents", "conversations", "document_id", "document_thumbnails"):
                st.session_state.pop(key, None)
            st.rerun()


def _render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        sources = message.get("sources") or []
        if sources:
            with st.expander(f"Sources ({len(sources)})"):
                for source in sources:
                    heading = source.get("filename") or f"Chunk {source.get('chunk_id', 0)}"
                    st.markdown(f"**{heading}**")
                    st.caption(source.get("text", ""))


def _render_empty_state() -> None:
    document_count = len(st.session_state.documents)
    if document_count:
        description = "Your documents are ready. Ask a question below to start a saved conversation."
        examples = "Try: “Summarize this document” · “What are the key obligations?” · “List the important dates”"
    else:
        description = "Upload a PDF or image from the sidebar, then ask questions grounded in its contents."
        examples = "Your conversations and documents stay private to this account."
    st.markdown(
        f'''<section class="empty-state">
          <div class="empty-state-icon">✦</div>
          <h2>What would you like to know?</h2>
          <p>{description}</p>
          <div class="empty-state-examples">{examples}</div>
        </section>''',
        unsafe_allow_html=True,
    )


def render_chat(cookie_manager) -> None:
    _refresh_collections()
    _render_sidebar(cookie_manager)

    title = st.session_state.get("conversation_title", "New chat")
    st.markdown(f'<div class="chat-title">{escape(title)}</div>', unsafe_allow_html=True)
    if st.session_state.messages:
        for message in st.session_state.messages:
            _render_message(message)
    else:
        _render_empty_state()

    prompt = st.chat_input("Ask about your documents…")
    if not prompt:
        return

    user_message = {"role": "user", "content": prompt, "sources": []}
    st.session_state.messages.append(user_message)
    _render_message(user_message)
    with st.chat_message("assistant"):
        with st.spinner("Searching your documents…"):
            ok, payload = ask(prompt, st.session_state.conversation_id, st.session_state.document_id)
        if ok:
            assistant_message = {"role": "assistant", "content": payload["answer"], "sources": payload.get("sources", [])}
            st.markdown(assistant_message["content"])
            sources = assistant_message["sources"]
            if sources:
                with st.expander(f"Sources ({len(sources)})"):
                    for source in sources:
                        st.caption(source.get("text", ""))
            st.session_state.messages.append(assistant_message)
            st.session_state.conversation_id = payload["conversation_id"]
            st.session_state.conversation_title = payload["conversation_title"]
            _refresh_collections()
        else:
            st.error(_detail(payload))
            st.session_state.messages.pop()
