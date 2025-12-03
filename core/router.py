# core/router.py

from typing import Optional

from .llm_agent import answer_user_from_prescription
from .locator import (
    EmergencyLocatorAgent,
    detect_locator_intent,
)


def handle_user_request(
    user_message: str,
    image_path: Optional[str] = None,
    locator_agent: Optional[EmergencyLocatorAgent] = None,
    radius_km: float = 5.0,
    user_address: Optional[str] = None,
) -> str:
    """
    Main entrypoint:
    - If user asks for nearest pharmacy/hospital → EmergencyLocatorAgent.
    - Else → prescription / medicine handling via Qwen + Llama.
    """

    # 1) Check locator intent
    intent = detect_locator_intent(user_message)
    if intent in ("pharmacy", "hospital"):
        if locator_agent is None:
            locator_agent = EmergencyLocatorAgent()

        places = locator_agent.get_nearest_places(
            place_kind=intent,
            radius_km=radius_km,
            address=user_address,
            use_ip_fallback=True,
        )
        label = "صيدليات" if intent == "pharmacy" else "مستشفيات"
        return locator_agent.format_places_for_chat(
            places=places,
            place_label=label,
            max_results=3,
        )

    # 2) Otherwise → prescription / medicine question
    return answer_user_from_prescription(
        image_path=image_path,
        user_question=user_message,
    )
