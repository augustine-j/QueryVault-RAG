import streamlit as st

from api import me
from auth_view import render_auth
from chat_view import render_chat
from session import clear_token, create_cookie_manager, load_token
from styles import inject_css

st.set_page_config(page_title="RAG Chat", page_icon="💬", layout="wide")
inject_css()

for key, value in {
    "token": None,
    "user": None,
    "conversation_id": None,
    "conversation_title": "New chat",
    "messages": [],
    "document_id": None,
    "documents": [],
    "conversations": [],
    "document_thumbnails": {},
}.items():
    st.session_state.setdefault(key, value)

cookie_manager = create_cookie_manager()
if not st.session_state.token:
    saved_token = load_token(cookie_manager)
    if saved_token:
        st.session_state.token = saved_token

if st.session_state.token and not st.session_state.user:
    ok, payload = me()
    if ok:
        st.session_state.user = payload
    else:
        clear_token(cookie_manager)
        st.session_state.token = None

if st.session_state.token and st.session_state.user:
    render_chat(cookie_manager)
else:
    render_auth(cookie_manager)
