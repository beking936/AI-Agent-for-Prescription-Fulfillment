# core/config.py

import os
from groq import Groq
from huggingface_hub import InferenceClient


# Try to load from Streamlit secrets first (when running `streamlit run app.py`)
try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = None

def _get_secret(name: str) -> str:
    """
    Read secret from:
    1) Streamlit secrets (if available)
    2) Environment variables (fallback)
    """
    if _secrets is not None and name in _secrets:
        return _secrets[name]
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} not set. Define it in .streamlit/secrets.toml or as an environment variable."
        )
    return value

GROQ_API_KEY = _get_secret("GROQ_API_KEY")
HF_TOKEN = _get_secret("HF_TOKEN")

QWEN_MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"
LLAMA_MODEL = "llama-3.3-70b-versatile"

client_qwen = InferenceClient(
    model=QWEN_MODEL_ID,
    token=HF_TOKEN,
)

groq_client = Groq(api_key=GROQ_API_KEY)
