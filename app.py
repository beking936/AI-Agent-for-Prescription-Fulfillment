import os
import tempfile
from PIL import Image
import streamlit as st

from core.router import handle_user_request
from core.locator import EmergencyLocatorAgent

# ---------- Brand assets ----------
LOGO_PATH = "assets/MediNexa_logo.jpg"  

page_icon = "💊"
if os.path.exists(LOGO_PATH):
    try:
        page_icon = Image.open(LOGO_PATH)
    except Exception:
        page_icon = "💊"

ASSISTANT_AVATAR = LOGO_PATH if os.path.exists(LOGO_PATH) else "🩺"
USER_AVATAR = "🙂"

# ---------- Page config ----------
st.set_page_config(
    page_title="MediNexa – AI Assistant",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    :root {
        --mn-bg: #b7dde2;
        --mn-bg-light: #dff4f6;
        --mn-primary: #0b8b97;
        --mn-primary-soft: #15aabf;
        --mn-primary-dark: #055d6a;
        --mn-border-soft: #97cdd1;
        --mn-text-main: #073b4c;
        --mn-text-muted: #4b6470;
    }

    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left,
            var(--mn-bg-light) 0,
            var(--mn-bg) 45%,
            var(--mn-bg) 100%);
    }
    [data-testid="stHeader"] { background: transparent; }

    .block-container {
        max-width: 1100px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        margin: 0 auto;
    }

    .mn-card {
        border-radius: 1.1rem;
        padding: 1rem 1.25rem;
        background: #ffffff;
        border: 1px solid rgba(151,205,209,0.95);
        box-shadow: 0 10px 25px rgba(7,59,76,0.15);
        margin-bottom: 1rem;
    }

    .mn-hero {
        border-radius: 1.35rem;
        padding: 1.1rem 1.4rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.96),
                                             rgba(223,244,246,0.98));
        border: 1px solid var(--mn-border-soft);
        box-shadow: 0 18px 55px rgba(7,59,76,0.25);
        margin-bottom: 1.5rem;
    }
    .mn-hero-pill {
        display:inline-flex;
        align-items:center;
        padding:0.2rem 0.8rem;
        border-radius:999px;
        font-size:0.78rem;
        letter-spacing:0.12em;
        text-transform:uppercase;
        color:var(--mn-primary-dark);
        background:rgba(183,221,226,0.7);
        border:1px solid rgba(151,205,209,0.9);
        margin-bottom:0.35rem;
    }
    .mn-hero-title {
        font-size:1.7rem;
        font-weight:700;
        color:var(--mn-text-main);
        margin-bottom:0.25rem;
    }
    .mn-hero-subtitle {
        font-size:0.96rem;
        color:var(--mn-text-muted);
        margin-bottom:0.65rem;
        max-width:32rem;
    }
    .mn-hero-footnote {
        font-size:0.78rem;
        color:var(--mn-text-muted);
        margin-top:0.25rem;
    }

    .mn-chat-header-row {
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:0.35rem;
    }
    .mn-chat-title {
        font-size:0.98rem;
        font-weight:600;
        color:var(--mn-text-main);
    }
    .mn-chat-subtitle {
        font-size:0.8rem;
        color:var(--mn-text-muted);
        margin-bottom:0.5rem;
    }

    .mn-status-pills {
        display:flex;
        flex-wrap:wrap;
        gap:0.3rem;
        margin-bottom:0.4rem;
    }
    .mn-status-pill {
        padding:0.12rem 0.6rem;
        border-radius:999px;
        font-size:0.7rem;
        border:1px solid rgba(151,205,209,0.9);
        background:rgba(223,244,246,0.9);
        color:var(--mn-text-main);
        display:inline-flex;
        align-items:center;
        gap:0.25rem;
    }
    .mn-status-pill-muted {
        opacity:0.7;
        background:rgba(248,250,252,0.9);
    }
    .mn-status-dot {
        width:6px;
        height:6px;
        border-radius:999px;
        background:#22c55e;
    }
    .mn-status-pill-muted .mn-status-dot {
        background:#9ca3af;
    }

    button[kind="primary"] {
        border-radius: 999px !important;
        padding: 0.35rem 1.2rem !important;
        font-weight: 600 !important;
        background-color: var(--mn-primary) !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background-color: var(--mn-primary-soft) !important;
    }

    /* Chat text readability */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {
        color: var(--mn-text-main) !important;
    }

    /* Right-side prescription card */
    .mn-side-title {
        font-size:0.9rem;
        font-weight:600;
        color:var(--mn-text-main);
        margin-bottom:0.2rem;
    }
    .mn-side-subtitle {
        font-size:0.78rem;
        color:var(--mn-text-muted);
        margin-bottom:0.6rem;
    }

    [data-testid="stFileUploader"] > section {
        border-radius: 0.75rem;
        border: 1px dashed rgba(151,205,209,0.9);
        background: rgba(255,255,255,0.9);
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi, I'm **MediNexa**.\n\n"
                "Upload a prescription and ask your question, and I’ll explain the medicines "
                "or help you find nearby pharmacies and hospitals."
            ),
        }
    ]

if "image_path" not in st.session_state:
    st.session_state.image_path = None

if "locator_agent" not in st.session_state:
    st.session_state.locator_agent = EmergencyLocatorAgent()

# ---------- Hero ----------
st.markdown('<div class="mn-hero">', unsafe_allow_html=True)
hero_cols = st.columns([2.2, 1.0])

with hero_cols[0]:
    st.markdown(
        """
        <div class="mn-hero-pill">MEDINEXA • AI ASSISTANT</div>
        <div class="mn-hero-title">Decode prescriptions. Find care faster.</div>
        <div class="mn-hero-subtitle">
          MediNexa reads handwritten prescriptions, explains your medicines in simple language,
          and helps you locate nearby pharmacies or hospitals.
        </div>
        <div class="mn-hero-footnote">
          ⚠️ MediNexa does not replace a real doctor or pharmacist. Always confirm treatment decisions with a professional.
        </div>
        """,
        unsafe_allow_html=True,
    )

with hero_cols[1]:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown(
            """
            <div style="
                display:flex;align-items:center;justify-content:center;
                height:100%;font-size:0.85rem;color:#4b6470;
                border-radius:1rem;border:1px dashed #97cdd1;
                background:rgba(255,255,255,0.9);">
                Place MediNexa logo at <code>assets/medinexa_logo.png</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Main content: Chat (left) + Prescription panel (right) ----------
st.markdown('<div class="mn-card">', unsafe_allow_html=True)
main_cols = st.columns([2.2, 1.2])

# ===== LEFT: CHAT =====
with main_cols[0]:
    # Header + status + reset
    top_cols = st.columns([2, 1])
    with top_cols[0]:
        st.markdown(
            """
            <div class="mn-chat-header-row">
              <div class="mn-chat-title">Chat with MediNexa</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_cols[1]:
        if st.button("🔄 New conversation", key="new_conv"):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        "New chat started ✨\n\n"
                        "Upload a prescription or just type your question to begin."
                    ),
                }
            ]
            st.session_state.image_path = None

    image_attached = st.session_state.image_path is not None

    st.markdown(
        f"""
        <div class="mn-status-pills">
          <div class="mn-status-pill{' mn-status-pill-muted' if not image_attached else ''}">
            <span class="mn-status-dot"></span>
            <span>{"Prescription attached" if image_attached else "No prescription yet"}</span>
          </div>
          <div class="mn-status-pill">
            <span class="mn-status-dot"></span>
            <span>Location: auto (IP based)</span>
          </div>
        </div>
        <div class="mn-chat-subtitle">
          Ask in Arabic or English. You can upload a prescription, then ask follow-up questions,
          or directly ask for the nearest pharmacy/hospital.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Existing messages
    for msg in st.session_state.messages:
        avatar = ASSISTANT_AVATAR if msg["role"] == "assistant" else USER_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat input (simple & clean)
    prompt = st.chat_input(
        "Type your question about medicines, side effects, or nearby pharmacies..."
    )

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            with st.spinner("Thinking..."):
                response = handle_user_request(
                    user_message=prompt,
                    image_path=st.session_state.image_path,
                    locator_agent=st.session_state.locator_agent,
                    user_address=None,  # always auto IP
                )
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

# ===== RIGHT: PRESCRIPTION PANEL =====
with main_cols[1]:
    st.markdown('<div class="mn-side-title">Prescription</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mn-side-subtitle">Attach or replace the current prescription. '
        'It will be used for all follow-up questions in this chat.</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload prescription image",
        type=["png", "jpg", "jpeg"],
        help="Supported formats: PNG, JPG, JPEG (up to 200 MB).",
    )

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(uploaded_file.read())
            st.session_state.image_path = tmp.name
        st.success("Prescription image updated for this conversation ✅")

    # Show a small preview if we have an image
    if st.session_state.image_path:
        st.image(
            st.session_state.image_path,
            caption="Current prescription (used for answers)",
            use_container_width=True,
        )
    else:
        st.info("No prescription attached yet. You can still ask general questions.")

st.markdown("</div>", unsafe_allow_html=True)
