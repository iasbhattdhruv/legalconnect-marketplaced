intent_keywords = {
    "divorce": [
        "divorce",
        "separate",
        "marriage problem",
        "mutual divorce"
    ],

    "aadhaar_update": [
        "aadhaar update",
        "update aadhaar",
        "aadhaar correction"
    ],

    "property_dispute": [
        "property dispute",
        "tenant problem",
        "land dispute"
    ],

    "cyber_crime": [
        "cyber crime",
        "online fraud",
        "scam"
    ],

    "pan_card": [
        "pan card",
        "apply pan",
        "pan application"
    ]
}


def detect_intent(user_input):

    text = user_input.lower()

    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return intent

    return None