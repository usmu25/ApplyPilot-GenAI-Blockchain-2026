import os
import requests
from dotenv import load_dotenv


load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://10.0.2.2:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


def generate_with_ollama(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=payload, timeout=180)
    response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()

