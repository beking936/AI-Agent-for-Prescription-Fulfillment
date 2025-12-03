
import json
from typing import Optional, Dict

from typing import Literal

from .config import groq_client, LLAMA_MODEL
from .ocr import call_qwen_model


Intent = Literal[
    "NO_PRESCRIPTION",
    "MED_INFO",
    "DOSING_EXPLANATION",
    "PHARMACY_LOCATOR",
    "OTHER",
]

def call_llama_for_prescription(
    prescription_json: Optional[Dict] = None,
    user_question: Optional[str] = None
) -> str:
    """
    Dual-mode:
    - If prescription_json is provided → explain / answer based on prescription.
    - If prescription_json is None → general medicine question only (text mode).
    """

    # Case 0: no info at all
    if prescription_json is None and user_question is None:
        return "Please either upload a prescription image or type your question about the medicine."

    # Case A: text-only medicine question (no JSON)
    if prescription_json is None:
        system_prompt = (
            "You are a helpful, careful AI pharmacist assistant.\n"
            "The user will ask questions about medicines.\n\n"
            "Your tasks:\n"
            "- Explain what the medicine is generally used for.\n"
            "- Explain common precautions in very general terms.\n"
            "- DO NOT give personal dosing or change any treatment.\n"
            "- DO NOT tell the user to start/stop/change any medicine.\n"
            "- Always mention that they must consult their doctor or pharmacist "
            "for personal medical advice.\n"
        )

        user_content = "User question about medicines:\n\n" + user_question

        completion = groq_client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=800,
        )
        return completion.choices[0].message.content.strip()

    # Case B: we have OCR JSON -> prescription explanation
    system_prompt = (
        "You are a helpful, careful AI pharmacist assistant.\n\n"
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
        "Your tasks:\n"
        "1. If the user asks a question, answer it using the JSON plus general medical knowledge.\n"
        "2. If there is no question, give a clear, patient-friendly explanation of the whole prescription.\n"
        "3. If an item looks like a device or hygiene product (e.g. mouthwash, electric brush), "
        "explain that it is part of oral care rather than a drug.\n"
        "4. If anything is unclear or the confidence is low (< 0.7), say it should be checked "
        "with a human pharmacist or doctor.\n"
        "5. Never invent dosages or durations that are not in the JSON.\n"
        "6. Always remind the user that this is not a substitute for a real doctor or pharmacist.\n"
    )

    if user_question is None:
        user_question = "Please explain this prescription in simple language for the patient."

    user_content = (
        "Here is the prescription JSON:\n\n"
        + json.dumps(prescription_json, indent=2)
        + "\n\nUser question:\n"
        + user_question
    )

    completion = groq_client.chat.completions.create(
        model=LLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=800,
    )
    return completion.choices[0].message.content.strip()

def answer_user_from_prescription(
    image_path: Optional[str] = None,
    user_question: Optional[str] = None,
) -> str:
    """
    - If image_path is provided → Qwen OCR + Llama.
    - Else → text-only question to Llama.
    """
    if image_path is not None:
        prescription_json = call_qwen_model(image_path)

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