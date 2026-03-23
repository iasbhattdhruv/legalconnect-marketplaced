from .intent_detector import detect_intent
from .knowledge_base import get_knowledge


def process_query(user_input):

    # Detect intent
    intent = detect_intent(user_input)

    # Get knowledge data
    data = get_knowledge(intent)

    # ✅ If knowledge exists → return smart structured response
    if data:
        data["google_search"] = f"https://www.google.com/search?q={user_input}"
        return data

    # ❌ If no knowledge → fallback to Google
    return {
        "advice": "I couldn't find exact structured guidance for your query. You can explore more here:",
        "steps": [],
        "links": [],
        "google_search": f"https://www.google.com/search?q={user_input}",
        "lawyer_type": None
    }