def get_ai_response(message):

    if not message:
        return "Please enter a valid question."

    google_link = f"https://www.google.com/search?q={message.replace(' ', '+')}"

    return f"""
Here is guidance for your query:

👉 {message}

You can follow these steps:
• Search official government website  
• Fill required forms  
• Upload documents if needed  

🔎 More info:
{google_link}
"""