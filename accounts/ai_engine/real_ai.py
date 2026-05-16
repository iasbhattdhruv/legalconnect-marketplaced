import json
import os
from urllib import request

API_KEY = os.getenv('OPENROUTER_API_KEY', '')


def get_ai_response(message):
    if not API_KEY:
        return "AI is currently unavailable because OPENROUTER_API_KEY is not configured."

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": "You are a smart Indian legal assistant. Give practical advice, steps, and helpful resources."
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    req = request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers
    )

    try:
        response = request.urlopen(req)
        result = json.loads(response.read().decode())

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        return "AI is currently unavailable. Please try again."
