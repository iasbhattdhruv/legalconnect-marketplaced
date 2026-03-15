from .intent_detector import detect_intent
from .knowledge_base import knowledge_base


def process_query(user_input):

    intent = detect_intent(user_input)

    if intent and intent in knowledge_base:

        data = knowledge_base[intent]

        return {
            "advice": data.get("advice"),
            "steps": data.get("steps"),
            "links": data.get("links")
        }

    # Fallback AI response
    return {
        "advice": "I couldn't fully understand the issue, but you may find useful information from the following official resources.",
        "steps": [
            "Search on official government portals",
            "Check if legal consultation is required",
            "Contact a lawyer if needed"
        ],
        "links": [
            "https://india.gov.in/",
            "https://districts.ecourts.gov.in/",
            "https://www.india.gov.in/topics/law-justice"
        ]
    }