import json
import re
from tools.gemini_client import generate_text


def clean_json_response(text: str) -> str:
    text = text.strip()

    # Remove markdown code fences if Gemini returns ```json ... ```
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # Try to extract JSON array
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:
        return text[start:end + 1]

    return text


def fallback_parse_results(raw_results: list, intake_result: dict) -> list:
    opportunities = []

    for item in raw_results:
        title = item.get("title", "Untitled opportunity")
        description = item.get("content", "")
        link = item.get("url", "")

        opportunities.append({
            "title": title,
            "organization": "Not clearly detected",
            "type": intake_result.get("opportunity_type", "General"),
            "field": intake_result.get("field", "Not specified"),
            "location": intake_result.get("location", "Not specified"),
            "requirements": ["Research", "Technical Skills", "Communication"],
            "description": description,
            "deadline": "Not clearly mentioned",
            "eligibility": "Not clearly mentioned",
            "link": link
        })

    return opportunities


def parse_opportunities_with_gemini(raw_results: list, intake_result: dict) -> list:
    if not raw_results:
        return []

    simplified_results = []

    for item in raw_results:
        simplified_results.append({
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "url": item.get("url", "")
        })

    prompt = f"""
You are an opportunity extraction agent for an AI application assistant.

User search intent:
Opportunity type: {intake_result.get("opportunity_type")}
Field: {intake_result.get("field")}
Location: {intake_result.get("location")}
User skills: {intake_result.get("skills_found")}

Raw web search results:
{json.dumps(simplified_results, indent=2)}

Task:
Extract clean opportunity data from these web results.

Return ONLY valid JSON.
Do not use markdown.
Do not explain anything.

Return a JSON array. Each object must follow this structure:

[
  {{
    "title": "Opportunity title",
    "organization": "University, company, or lab name",
    "type": "Academic / Internship / Job / General",
    "field": "Relevant field",
    "location": "Country or city if available",
    "requirements": ["skill 1", "skill 2", "skill 3"],
    "description": "Short 1-2 sentence summary",
    "deadline": "Deadline if available, otherwise Not clearly mentioned",
    "eligibility": "Eligibility if available, otherwise Not clearly mentioned",
    "link": "Original URL"
  }}
]

Rules:
- Do not invent fake deadlines.
- Do not invent fake eligibility.
- If information is missing, write "Not clearly mentioned".
- Keep requirements short and practical.
- Preserve the original URL.
"""

    try:
        response = generate_text(prompt)
        cleaned = clean_json_response(response)
        parsed = json.loads(cleaned)

        if isinstance(parsed, list) and parsed:
            return parsed

        return fallback_parse_results(raw_results, intake_result)

    except Exception as error:
        print(f"Gemini opportunity parsing failed. Error: {error}")
        return fallback_parse_results(raw_results, intake_result)
