# # core/router.py

# from typing import Optional

# from .llm_agent import answer_user_from_prescription
# from .locator import (
#     EmergencyLocatorAgent,
#     detect_locator_intent,
# )


# def handle_user_request(
#     user_message: str,
#     image_path: Optional[str] = None,
#     locator_agent: Optional[EmergencyLocatorAgent] = None,
#     radius_km: float = 5.0,
#     user_address: Optional[str] = None,
# ) -> str:
#     """
#     Main entrypoint:
#     - If user asks for nearest pharmacy/hospital → EmergencyLocatorAgent.
#     - Else → prescription / medicine handling via Qwen + Llama.
#     """

#     # 1) Check locator intent
#     intent = detect_locator_intent(user_message)
#     if intent in ("pharmacy", "hospital"):
#         if locator_agent is None:
#             locator_agent = EmergencyLocatorAgent()

#         places = locator_agent.get_nearest_places(
#             place_kind=intent,
#             radius_km=radius_km,
#             address=user_address,
#             use_ip_fallback=True,
#         )
#         label = "صيدليات" if intent == "pharmacy" else "مستشفيات"
#         return locator_agent.format_places_for_chat(
#             places=places,
#             place_label=label,
#             max_results=3,
#         )

#     # 2) Otherwise → prescription / medicine question
#     return answer_user_from_prescription(
#         image_path=image_path,
#         user_question=user_message,
#     )


# update file 

# core/router.py

from typing import Optional, Literal

from .llm_agent import answer_user_from_prescription
from .locator import (
    EmergencyLocatorAgent,
    detect_locator_intent,
)

LocatorIntent = Literal["pharmacy", "hospital"]


def _fallback_locator_intent(user_message: str) -> Optional[LocatorIntent]:
    """
    Simple keyword-based backup intent detection.

    This is used when detect_locator_intent() returns no intent,
    so that common phrases like "nearest pharmacy from me" still work
    even if spelling is bad or the LLM-based detector is too strict.
    """
    text = user_message.lower()

    # Pharmacy patterns (English + Arabic + common misspellings)
    pharmacy_keywords = [
        "nearest pharmacy",
        "pharmacy near me",
        "pharmcy",           # common typo
        "pharmarcy",
        "صيدلية",
        "صيدليات",
    ]

    # Hospital patterns (English + Arabic)
    hospital_keywords = [
        "nearest hospital",
        "hospital near me",
        "emergency hospital",
        "مستشفى",
        "مستشفيات",
    ]

    if any(k in text for k in pharmacy_keywords):
        return "pharmacy"
    if any(k in text for k in hospital_keywords):
        return "hospital"

    return None


def _handle_locator_request(
    intent: LocatorIntent,
    locator_agent: EmergencyLocatorAgent,
    radius_km: float,
    user_address: Optional[str],
) -> str:
    """
    Handles the 'nearest pharmacy / hospital' flow.
    Returns a user-friendly message even when no places are found.
    """
    places = locator_agent.get_nearest_places(
        place_kind=intent,
        radius_km=radius_km,
        address=user_address,
        use_ip_fallback=True,
    )

    label_ar = "صيدليات" if intent == "pharmacy" else "مستشفيات"
    label_en = "pharmacies" if intent == "pharmacy" else "hospitals"

    if not places:
        # Graceful fallback if nothing is found or locator fails.
        if user_address:
            return (
                f"لم أستطع العثور على أي {label_ar} قريبة من العنوان الذي أدخلته ضمن دائرة نصف قطرها "
                f"{radius_km} كم.\n\n"
                f"**Suggestions / اقتراحات:**\n"
                f"- تأكد من أن العنوان مكتوب بشكل أوضح (مثال: شارع + مدينة).\n"
                f"- جرّب زيادة نصف القطر المسموح به.\n"
                f"- يمكنك أيضًا البحث يدويًا في خرائط جوجل عن `{label_en} near {user_address}`."
            )
        else:
            return (
                f"لم أستطع تحديد موقعك للبحث عن {label_ar} قريبة.\n\n"
                f"من فضلك أدخل عنوانك (المدينة + الشارع أو أقرب معلم) في خانة العنوان على اليسار، "
                f"ثم اسألني مرة أخرى عن أقرب {label_ar}."
            )

    # We have results → format them nicely for chat.
    return locator_agent.format_places_for_chat(
        places=places,
        place_label=label_ar,
        max_results=3,
    )


def handle_user_request(
    user_message: str,
    image_path: Optional[str] = None,
    locator_agent: Optional[EmergencyLocatorAgent] = None,
    radius_km: float = 5.0,
    user_address: Optional[str] = None,
) -> str:
    """
    Main entrypoint used by the Streamlit app.

    Logic:
    1. Try to detect if the user is asking for nearest pharmacy/hospital.
       - First use detect_locator_intent (your main detector).
       - If that fails, use a simple keyword-based fallback.
    2. If location intent is detected → use EmergencyLocatorAgent.
    3. Otherwise → handle prescription / medicine questions via LLM.
    """

    # 1) Try primary intent detection
    intent: Optional[LocatorIntent] = detect_locator_intent(user_message)  # type: ignore[assignment]

    # 2) Fallback heuristic if detector returns nothing/unknown
    if intent not in ("pharmacy", "hospital"):
        intent = _fallback_locator_intent(user_message)

    # 3) Location / nearest-place path
    if intent in ("pharmacy", "hospital"):
        if locator_agent is None:
            locator_agent = EmergencyLocatorAgent()

        return _handle_locator_request(
            intent=intent,
            locator_agent=locator_agent,
            radius_km=radius_km,
            user_address=user_address,
        )

    # 4) Otherwise → prescription / medicine question
    return answer_user_from_prescription(
        image_path=image_path,
        user_question=user_message,
    )
