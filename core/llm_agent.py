
# import json
# from typing import Optional, Dict

# from typing import Literal

# from .config import groq_client, LLAMA_MODEL
# from .ocr import call_qwen_model


# Intent = Literal[
#     "NO_PRESCRIPTION",
#     "MED_INFO",
#     "DOSING_EXPLANATION",
#     "PHARMACY_LOCATOR",
#     "OTHER",
# ]

# def call_llama_for_prescription(
#     prescription_json: Optional[Dict] = None,
#     user_question: Optional[str] = None
# ) -> str:
#     """
#     Dual-mode:
#     - If prescription_json is provided → explain / answer based on prescription.
#     - If prescription_json is None → general medicine question only (text mode).
#     """

#     # Case 0: no info at all
#     if prescription_json is None and user_question is None:
#         return "Please either upload a prescription image or type your question about the medicine."

#     # Case A: text-only medicine question (no JSON)
#     if prescription_json is None:
#         system_prompt = (
#             "You are a helpful, careful AI pharmacist assistant.\n"
#             "The user will ask questions about medicines.\n\n"
#             "Your tasks:\n"
#             "- Explain what the medicine is generally used for.\n"
#             "- Explain common precautions in very general terms.\n"
#             "- DO NOT give personal dosing or change any treatment.\n"
#             "- DO NOT tell the user to start/stop/change any medicine.\n"
#             "- Always mention that they must consult their doctor or pharmacist "
#             "for personal medical advice.\n"
#         )

#         user_content = "User question about medicines:\n\n" + user_question

#         completion = groq_client.chat.completions.create(
#             model=LLAMA_MODEL,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_content},
#             ],
#             temperature=0.1,
#             max_tokens=800,
#         )
#         return completion.choices[0].message.content.strip()

#     # Case B: we have OCR JSON -> prescription explanation
#     system_prompt = (
#         "You are a helpful, careful AI pharmacist assistant.\n\n"
#         "You receive a JSON object called `prescription` with a list of medications.\n"
#         "Each medication may contain:\n"
#         "- raw_text\n"
#         "- drug_name\n"
#         "- strength\n"
#         "- dose\n"
#         "- frequency\n"
#         "- duration\n"
#         "- instructions\n"
#         "- confidence (0–1, how sure the OCR is)\n\n"
#         "Your tasks:\n"
#         "1. If the user asks a question, answer it using the JSON plus general medical knowledge.\n"
#         "2. If there is no question, give a clear, patient-friendly explanation of the whole prescription.\n"
#         "3. If an item looks like a device or hygiene product (e.g. mouthwash, electric brush), "
#         "explain that it is part of oral care rather than a drug.\n"
#         "4. If anything is unclear or the confidence is low (< 0.7), say it should be checked "
#         "with a human pharmacist or doctor.\n"
#         "5. Never invent dosages or durations that are not in the JSON.\n"
#         "6. Always remind the user that this is not a substitute for a real doctor or pharmacist.\n"
#     )

#     if user_question is None:
#         user_question = "Please explain this prescription in simple language for the patient."

#     user_content = (
#         "Here is the prescription JSON:\n\n"
#         + json.dumps(prescription_json, indent=2)
#         + "\n\nUser question:\n"
#         + user_question
#     )

#     completion = groq_client.chat.completions.create(
#         model=LLAMA_MODEL,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_content},
#         ],
#         temperature=0.1,
#         max_tokens=800,
#     )
#     return completion.choices[0].message.content.strip()

# def answer_user_from_prescription(
#     image_path: Optional[str] = None,
#     user_question: Optional[str] = None,
# ) -> str:
#     """
#     - If image_path is provided → Qwen OCR + Llama.
#     - Else → text-only question to Llama.
#     """
#     if image_path is not None:
#         prescription_json = call_qwen_model(image_path)

#         if prescription_json.get("illegible"):
#             return (
#                 "I could not reliably read this prescription image. "
#                 "Please upload a clearer photo or consult your doctor/pharmacist directly."
#             )

#         return call_llama_for_prescription(
#             prescription_json=prescription_json,
#             user_question=user_question,
#         )

#     # No image → pure text question about medicines
#     return call_llama_for_prescription(
#         prescription_json=None,
#         user_question=user_question,
#     )


# core/llm_agent.py

import json
from typing import Optional, Dict, Literal

from .config import groq_client, LLAMA_MODEL
from .ocr import call_qwen_model


Intent = Literal[
    "NO_PRESCRIPTION",
    "MED_INFO",
    "DOSING_EXPLANATION",
    "PHARMACY_LOCATOR",
    "OTHER",
]


# ------------------------- Helpers -------------------------


def _is_arabic(text: str) -> bool:
    """Very simple check: does the text contain Arabic characters?"""
    if not text:
        return False
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


def _call_llama(messages, max_tokens: int = 800) -> str:
    """
    Thin wrapper around Groq LLaMA call.
    Returns a safe error message instead of raising if the API fails.
    """
    try:
        completion = groq_client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens,
        )
        content = completion.choices[0].message.content
        return (content or "").strip()
    except Exception as e:
        # Fallback message if the LLM API fails
        return (
            "Sorry, there was a technical problem while generating the answer. "
            "Please try again in a moment or consult your doctor/pharmacist directly.\n\n"
            f"(Internal error: {e})"
        )


# ---------------------- Main LLaMA logic ----------------------


def call_llama_for_prescription(
    prescription_json: Optional[Dict] = None,
    user_question: Optional[str] = None,
) -> str:
    """
    Dual-mode:
      - If prescription_json is provided → explain / answer based on prescription.
      - If prescription_json is None → general medicine question only (text mode).
    """

    # ---------- Case 0: nothing at all ----------
    if prescription_json is None and (user_question is None or not user_question.strip()):
        return "Please either upload a prescription image or type your question about the medicine."

    # Normalize question (but don't invent a 'safe' one)
    question_text = (user_question or "").strip()

    # Detect language from whatever the user actually wrote
    user_is_arabic = _is_arabic(question_text)

    # ---------- Case A: text-only medicine question (no JSON) ----------
    if prescription_json is None:
        system_prompt = (
            "You are a careful, concise AI pharmacist assistant.\n"
            "The user asks general questions about medicines.\n\n"
            "Your behavior:\n"
            "- Answer in the SAME LANGUAGE as the user (Arabic or English).\n"
            "- Keep answers structured and short:\n"
            "  1) What it is used for (brief)\n"
            "  2) Common precautions (bullet points)\n"
            "  3) Very general notes (no personal decisions)\n"
            "- DO NOT give personal dosing advice, and do not tell the user to start, stop, "
            "or change any treatment.\n"
            "- If the user asks for something that requires a doctor (like changing dose, "
            "combining many medicines, or pregnancy-specific decisions), clearly say they "
            "must talk to their doctor or pharmacist.\n"
            "- Always end with a short disclaimer that this is not a substitute for a real doctor.\n"
        )

        if user_is_arabic:
            system_prompt += "\nYou MUST reply in Arabic.\n"
        else:
            system_prompt += "\nYou MUST reply in English.\n"

        user_content = "User question about medicines:\n\n" + question_text

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return _call_llama(messages)

    # ---------- Case B: we have prescription JSON ----------
    system_prompt = (
        "You are a careful AI pharmacist assistant.\n\n"
        "You receive a JSON object called `prescription` with a list of medications.\n"
        "Each medication may contain:\n"
        "- raw_text\n"
        "- drug_name\n"
        "- strength\n"
        "- dose\n"
        "- frequency\n"
        "- duration\n"
        "- instructions\n"
        "- confidence (0–1, how sure the OCR is)\n\n"
        "Your behavior:\n"
        "- Answer in the SAME LANGUAGE as the user (Arabic or English) if there is a question.\n"
        "- Use the JSON as the main source of truth.\n"
        "- Do NOT invent dosages or durations that are not present in the JSON.\n"
        "- If confidence < 0.7 or something looks unclear, explicitly say it should be "
        "checked with a human pharmacist or doctor.\n"
        "- If there is no specific question, give a short, patient-friendly explanation of the prescription.\n"
        "- Structure your answer as:\n"
        "  1) Summary of all medicines (bullet list)\n"
        "  2) How to take them (only if it is clearly in the JSON)\n"
        "  3) General precautions (very generic)\n"
        "  4) Strong disclaimer to see a real doctor/pharmacist.\n"
    )

    # For the pure “no question, just JSON” case, we may not detect language.
    if user_is_arabic:
        system_prompt += "\nIf possible, reply in Arabic.\n"
    else:
        system_prompt += "\nIf possible, reply in English.\n"

    # Build user content: always send the JSON;
    # only add the question block if the user actually asked something.
    user_content = "Here is the prescription JSON:\n\n" + json.dumps(
        prescription_json, indent=2, ensure_ascii=False
    )

    if question_text:
        user_content += "\n\nUser question:\n" + question_text
    else:
        # No explicit question → let the model decide,
        # guided only by the system prompt rule "If there is no question, explain..."
        user_content += "\n\n(No explicit user question was provided.)"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return _call_llama(messages)


# ---------------------- Public entrypoint ----------------------


def answer_user_from_prescription(
    image_path: Optional[str] = None,
    user_question: Optional[str] = None,
) -> str:
    """
    - If image_path is provided → Qwen OCR + LLaMA explanation.
    - Else → text-only question to LLaMA.
    """

    if image_path is not None:
        try:
            prescription_json = call_qwen_model(image_path) or {}
        except Exception as e:
            return (
                "I couldn't process this prescription image due to a technical error. "
                "Please try uploading a clearer image or ask your question again.\n\n"
                f"(Internal error from OCR: {e})"
            )

        if prescription_json.get("illegible"):
            return (
                "I could not reliably read this prescription image. "
                "Please upload a clearer photo or consult your doctor/pharmacist directly."
            )

        return call_llama_for_prescription(
            prescription_json=prescription_json,
            user_question=user_question,
        )

    # No image → pure text question about medicines
    return call_llama_for_prescription(
        prescription_json=None,
        user_question=user_question,
    )
