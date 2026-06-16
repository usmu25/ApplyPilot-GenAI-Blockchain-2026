import os
from dotenv import load_dotenv
from tavily import TavilyClient

from tools.ollama_client import generate_with_ollama


load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


REALTIME_KEYWORDS = [
    "current",
    "latest",
    "today",
    "now",
    "weather",
    "news",
    "recent",
    "update",
    "price",
    "deadline",
    "2026",
    "2027"
]


APPLICATION_KEYWORDS = [
    "cv",
    "resume",
    "cover letter",
    "job",
    "internship",
    "phd",
    "masters",
    "position",
    "opportunity",
    "application",
    "apply"
]


def needs_realtime_search(message: str) -> bool:
    message = message.lower()
    return any(keyword in message for keyword in REALTIME_KEYWORDS)


def is_application_related(message: str) -> bool:
    message = message.lower()
    return any(keyword in message for keyword in APPLICATION_KEYWORDS)


def get_tavily_context(query: str) -> str:
    if not TAVILY_API_KEY:
        return ""

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=4
        )

        results = response.get("results", [])

        context_parts = []

        for item in results:
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")

            context_parts.append(
                f"Title: {title}\nURL: {url}\nContent: {content}"
            )

        return "\n\n".join(context_parts)

    except Exception as error:
        print(f"Tavily search failed in chat agent: {error}")
        return ""


def run_chat_agent(user_message: str) -> str:
    message = user_message.strip()

    if not message:
        return "Please send a message."

    lower_message = message.lower()

    if lower_message in ["hi", "hello", "hey", "salam", "assalamualaikum", "assalam o alaikum"]:
        return (
            "Hello! I am ApplyPilot.\n\n"
            "You can chat with me normally, or use /campaign for the application workflow."
        )

    if is_application_related(message):
        prompt = f"""
You are ApplyPilot, a helpful AI assistant.

The user asked:
{message}

The user may be asking about jobs, internships, PhD positions, CVs, cover letters, or applications.

Reply naturally, but also guide them to the correct ApplyPilot workflow when useful:
- /campaign for complete application workflow
- /search for only searching opportunities
- /apply for the older CV workflow

Keep the answer helpful and concise.
"""
        return generate_with_ollama(prompt)

    web_context = ""

    if needs_realtime_search(message):
        web_context = get_tavily_context(message)

    prompt = f"""
You are ApplyPilot, a helpful general-purpose AI chat assistant.

You can:
- Answer general questions
- Explain concepts
- Help with study and writing
- Discuss current information if web context is provided
- Guide users to /campaign for application workflow

User message:
{message}

Web context:
{web_context if web_context else "No live web context used."}

Instructions:
- If web context is available, use it.
- If web context is not available and the question needs real-time data, say you may not have enough current data.
- For application tasks, mention /campaign when relevant.
- Keep the answer clear, natural, and not too long.
"""

    try:
        return generate_with_ollama(prompt)
    except Exception as error:
        print(f"Ollama chat failed: {error}")
        return (
            "I had trouble generating a response from Ollama. "
            "Please check if Ollama is running and reachable."
        )
