import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def generate_text(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing in .env file")

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    if not response.text:
        return ""

    return response.text.strip()
