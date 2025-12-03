# app.py

import tempfile
import streamlit as st

from core.router import handle_user_request
from core.locator import EmergencyLocatorAgent

st.set_page_config(page_title="PharmaBot", page_icon="💊")

st.title("💊 PharmaBot – Prescription & Pharmacy Assistant")

st.markdown(
    "Upload a prescription image **or** just ask a question about medicines.\n\n"
    "You can also ask for the *nearest pharmacy/hospital*."
)

locator_agent = EmergencyLocatorAgent()

# 1) Image upload
uploaded_file = st.file_uploader("📷 Upload prescription image (optional)", type=["png", "jpg", "jpeg"])

image_path = None
if uploaded_file:
    # Save to a temporary file for OCR
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(uploaded_file.read())
        image_path = tmp.name

# 2) Address for better location accuracy (optional)
user_address = st.text_input("📍 Your address (optional, for nearest pharmacy/hospital)", "")

# 3) User message
user_message = st.text_area("💬 Your question or request:", "")

if st.button("Ask"):
    if not user_message and not image_path:
        st.warning("Please type a question or upload an image.")
    else:
        with st.spinner("Thinking..."):
            response = handle_user_request(
                user_message=user_message or "",
                image_path=image_path,
                locator_agent=locator_agent,
                user_address=user_address or None,
            )
        st.markdown("### 🤖 Response")
        st.write(response)
