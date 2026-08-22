"""Authentication screen."""

import streamlit as st

from api import login, register
from session import save_token


# ============================================================
# HELPERS
# ============================================================

def _detail(payload: object) -> str:
    if isinstance(payload, dict):
        return payload.get("detail", "Request failed.")
    return "Request failed."


def _store_session(payload: dict, cookie_manager) -> None:
    st.session_state.token = payload["access_token"]
    st.session_state.user = payload["user"]
    st.session_state.conversation_id = None
    st.session_state.messages = []

    save_token(cookie_manager, payload["access_token"])

    st.rerun()


# ============================================================
# CSS
# ============================================================

def _inject_css() -> None:
    st.markdown(
        """
<style>

.stApp {
    background:
        radial-gradient(
            circle at 12% 20%,
            rgba(99, 102, 241, 0.16),
            transparent 30%
        ),
        radial-gradient(
            circle at 88% 80%,
            rgba(139, 92, 246, 0.12),
            transparent 30%
        ),
        #080b14;
    color: #f8fafc;
}

.block-container {
    max-width: 1180px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* Hide Streamlit chrome */

#MainMenu {
    visibility: hidden;
}

header {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ==========================================================
   LEFT SIDE
   ========================================================== */

.brand-section {
    padding: 3rem 2rem 3rem 1rem;
}

.brand-badge {
    display: inline-block;
    padding: 7px 13px;
    border-radius: 999px;

    background: rgba(99, 102, 241, 0.10);
    border: 1px solid rgba(129, 140, 248, 0.22);

    color: #c7d2fe;

    font-size: 13px;
    font-weight: 600;

    margin-bottom: 24px;
}

.brand-title {
    font-size: 52px;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -2px;

    margin-bottom: 18px;

    background: linear-gradient(
        135deg,
        #ffffff 0%,
        #c7d2fe 55%,
        #a78bfa 100%
    );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-description {
    max-width: 520px;

    color: #94a3b8;

    font-size: 17px;
    line-height: 1.7;

    margin-bottom: 30px;
}

.feature {
    display: flex;
    align-items: center;

    gap: 13px;

    margin: 17px 0;

    color: #cbd5e1;

    font-size: 14px;
}

.feature-icon {
    width: 36px;
    height: 36px;

    flex-shrink: 0;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    background: rgba(99, 102, 241, 0.12);

    border: 1px solid rgba(129, 140, 248, 0.15);

    color: #a5b4fc;
}


/* ==========================================================
   AUTH HEADER
   ========================================================== */

.auth-header {
    padding: 30px 32px 10px 32px;

    background: rgba(15, 23, 42, 0.78);

    border-top-left-radius: 24px;
    border-top-right-radius: 24px;

    border: 1px solid rgba(148, 163, 184, 0.14);
    border-bottom: none;

    box-shadow:
        0 25px 70px rgba(0, 0, 0, 0.30);

    backdrop-filter: blur(18px);
}

.auth-logo {
    width: 48px;
    height: 48px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 14px;

    margin-bottom: 18px;

    background: linear-gradient(
        135deg,
        #6366f1,
        #8b5cf6
    );

    color: white;

    font-size: 21px;
    font-weight: 800;

    box-shadow:
        0 10px 30px rgba(99, 102, 241, 0.30);
}

.auth-title {
    color: #f8fafc;

    font-size: 28px;
    font-weight: 750;

    margin-bottom: 7px;
}

.auth-subtitle {
    color: #94a3b8;

    font-size: 14px;
    line-height: 1.5;

    padding-bottom: 18px;
}


/* ==========================================================
   AUTH BODY
   ========================================================== */

div[data-testid="stVerticalBlock"] {
    gap: 0.35rem;
}


/* ==========================================================
   TABS
   ========================================================== */

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;

    background: rgba(15, 23, 42, 0.78);

    padding: 5px 30px;

    border-left: 1px solid rgba(148, 163, 184, 0.14);
    border-right: 1px solid rgba(148, 163, 184, 0.14);

    margin: 0;
}

.stTabs [data-baseweb="tab"] {
    flex: 1;

    justify-content: center;

    color: #94a3b8;

    font-size: 13px;
    font-weight: 600;

    padding: 10px 14px;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #e2e8f0;
}

.stTabs [aria-selected="true"] {
    color: white !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: #8b5cf6;
}


/* ==========================================================
   FORM AREA
   ========================================================== */

div[data-testid="stForm"] {
    background: rgba(15, 23, 42, 0.78);

    border: 1px solid rgba(148, 163, 184, 0.14);

    border-top: none;

    border-bottom-left-radius: 24px;
    border-bottom-right-radius: 24px;

    padding: 20px 30px 30px 30px;

    box-shadow:
        0 25px 70px rgba(0, 0, 0, 0.30);
}


/* ==========================================================
   LABELS
   ========================================================== */

.auth-field-label {
    color: #cbd5e1;

    font-size: 13px;

    font-weight: 600;

    margin-top: 12px;
    margin-bottom: 6px;
}


/* ==========================================================
   INPUTS
   ========================================================== */

div[data-baseweb="input"] {
    background: rgba(15, 23, 42, 0.85) !important;

    border: 1px solid rgba(148, 163, 184, 0.16) !important;

    border-radius: 11px !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: #6366f1 !important;

    box-shadow:
        0 0 0 3px rgba(99, 102, 241, 0.12) !important;
}

div[data-baseweb="input"] input {
    background: transparent !important;

    color: #f8fafc !important;

    font-size: 14px !important;
}

div[data-baseweb="input"] input::placeholder {
    color: #64748b !important;
}


/* ==========================================================
   BUTTON
   ========================================================== */

.stFormSubmitButton button {
    margin-top: 14px;

    min-height: 46px;

    border: 0 !important;

    border-radius: 11px !important;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #8b5cf6
        ) !important;

    color: white !important;

    font-size: 14px !important;

    font-weight: 700 !important;

    box-shadow:
        0 10px 24px rgba(99, 102, 241, 0.24);

    transition: 0.15s ease;
}

.stFormSubmitButton button:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
}


/* ==========================================================
   ALERTS
   ========================================================== */

div[data-testid="stAlert"] {
    border-radius: 11px;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 900px) {

    .brand-section {
        display: none;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1.5rem;
    }
}

</style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# AUTH SCREEN
# ============================================================

def render_auth(cookie_manager) -> None:

    _inject_css()

    left, right = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    # ========================================================
    # LEFT SIDE
    # ========================================================

    with left:

        st.html(
            """
            <div class="brand-section">

                <div class="brand-badge">
                    ✦ AI-Powered Document Assistant
                </div>

                <div class="brand-title">
                    Chat with your<br>
                    knowledge base.
                </div>

                <div class="brand-description">
                    Upload your private documents and ask questions
                    using intelligent retrieval-augmented generation.
                    Get answers grounded in your own data.
                </div>

                <div class="feature">
                    <div class="feature-icon">
                        ✦
                    </div>

                    <div>
                        <strong>Grounded answers</strong><br>
                        <span style="color:#64748b;">
                            Responses are based on retrieved context.
                        </span>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">
                        ⌕
                    </div>

                    <div>
                        <strong>Semantic search</strong><br>
                        <span style="color:#64748b;">
                            Find relevant information beyond keywords.
                        </span>
                    </div>
                </div>

                <div class="feature">
                    <div class="feature-icon">
                        ◈
                    </div>

                    <div>
                        <strong>Private knowledge</strong><br>
                        <span style="color:#64748b;">
                            Keep your document-based conversations organized.
                        </span>
                    </div>
                </div>

            </div>
            """
        )

    # ========================================================
    # RIGHT SIDE
    # ========================================================

    with right:

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        st.html(
            """
            <div class="auth-header">

                <div class="auth-logo">
                    RAG 
                </div>

                <div class="auth-title">
                    Welcome 
                </div>

                <div class="auth-subtitle">
                    Sign in or login to continue to your knowledge workspace.
                </div>

            </div>
            """
        )

        # ----------------------------------------------------
        # Tabs
        # ----------------------------------------------------

        sign_in, create_account = st.tabs(
            ["Sign in", "Create account"]
        )

        # ====================================================
        # SIGN IN
        # ====================================================

        with sign_in:

            with st.form("login_form"):

                st.markdown(
                    '<p class="auth-field-label">'
                    'Email address'
                    '</p>',
                    unsafe_allow_html=True,
                )

                email = st.text_input(
                    "Email address",
                    key="login_email",
                    placeholder="you@example.com",
                    label_visibility="collapsed",
                )

                st.markdown(
                    '<p class="auth-field-label">'
                    'Password'
                    '</p>',
                    unsafe_allow_html=True,
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                    placeholder="Enter your password",
                    label_visibility="collapsed",
                )

                submitted = st.form_submit_button(
                    "Sign in →",
                    use_container_width=True,
                )

            if submitted:

                if not email or not password:

                    st.error(
                        "Enter your email address and password."
                    )

                else:

                    ok, payload = login(
                        email,
                        password,
                    )

                    if ok:

                        _store_session(
                            payload,
                            cookie_manager,
                        )

                    else:

                        st.error(
                            _detail(payload)
                        )

        # ====================================================
        # CREATE ACCOUNT
        # ====================================================

        with create_account:

            with st.form("register_form"):

                st.markdown(
                    '<p class="auth-field-label">'
                    'Name <span style="color:#64748b;">'
                    '(optional)'
                    '</span>'
                    '</p>',
                    unsafe_allow_html=True,
                )

                full_name = st.text_input(
                    "Name (optional)",
                    key="register_name",
                    placeholder="Your name",
                    label_visibility="collapsed",
                )

                st.markdown(
                    '<p class="auth-field-label">'
                    'Email address'
                    '</p>',
                    unsafe_allow_html=True,
                )

                email = st.text_input(
                    "Email address",
                    key="register_email",
                    placeholder="you@example.com",
                    label_visibility="collapsed",
                )

                st.markdown(
                    '<p class="auth-field-label">'
                    'Password'
                    '</p>',
                    unsafe_allow_html=True,
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="register_password",
                    placeholder="At least 8 characters",
                    help="Passwords can be up to 72 UTF-8 bytes.",
                    label_visibility="collapsed",
                )

                submitted = st.form_submit_button(
                    "Create account →",
                    use_container_width=True,
                )

            if submitted:

                if not email or len(password) < 8:

                    st.error(
                        "Use a valid email and a password "
                        "of at least 8 characters."
                    )

                else:

                    ok, payload = register(
                        email,
                        password,
                        full_name,
                    )

                    if ok:

                        _store_session(
                            payload,
                            cookie_manager,
                        )

                    else:

                        st.error(
                            _detail(payload)
                        )