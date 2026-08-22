import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.35rem; padding-bottom: 5rem; max-width: 960px;}
        section[data-testid="stSidebar"] {background: #15181e;}
        section[data-testid="stSidebar"] .block-container {padding-top: 1.3rem;}
        .app-brand {font-size: 1.12rem; font-weight: 700; letter-spacing: .02em; margin-bottom: .8rem;}
        .section-label {color: #969aa3; font-size: .72rem; font-weight: 700; letter-spacing: .08em; margin: 1.2rem 0 .45rem;}
        .chat-title {font-size: 1.25rem; font-weight: 650; margin-bottom: 1rem;}
        div[data-testid="stVerticalBlockBorderWrapper"] {border-color: #303641; border-radius: 16px; background: #12151b;}
        .auth-field-label {margin: .7rem 0 .35rem; color: #e8e2dc; font-size: .88rem; font-weight: 600;}
        .auth-field-label span {color: #949aa4; font-weight: 400;}
        div[data-testid="stTextInput"] input {min-height: 2.7rem; line-height: 1.35rem;}
        div[data-testid="stTextInput"] input::placeholder {color: #8d939d; opacity: 1;}
        /* Streamlit's password-eye button overlaps text at some zoom levels. */
        div[data-testid="stTextInput"] button[aria-label="Show password text"],
        div[data-testid="stTextInput"] button[aria-label="Hide password text"] {display: none !important;}
        .empty-state {max-width: 620px; margin: 15vh auto 0; padding: 2.2rem; text-align: center; border: 1px solid #2d323b; border-radius: 16px; background: #12151b;}
        .empty-state-icon {color: #d68d5d; font-size: 1.6rem; margin-bottom: .6rem;}
        .empty-state h2 {font-size: 1.45rem; margin: 0 0 .6rem;}
        .empty-state p {color: #b5b8bf; margin: 0 auto .8rem; line-height: 1.55;}
        .empty-state-examples {color: #8e949e; font-size: .88rem; line-height: 1.55;}
        [data-testid="stChatMessage"] {border-radius: 12px; padding: .55rem .8rem;}
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {background: #352a25;}
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {border-left: 2px solid #4c515b;}
        div[data-testid="stExpander"] {border-color: #333842; background: transparent;}
        .stButton > button {border-radius: 8px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
