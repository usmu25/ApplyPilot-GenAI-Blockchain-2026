from tools.ollama_client import generate_with_ollama


def refine_cv_with_ollama(cv_text: str, opportunity: dict) -> str:
    prompt = f"""
You are an expert academic CV editor.

Your task is to rewrite the user's CV for the specific opportunity below.

STRICT OUTPUT RULES:
- Output ONLY the final CV content.
- Do NOT say "Here is a refined version".
- Do NOT include "I made the following changes".
- Do NOT include notes, comments, explanations, placeholders, or warnings.
- Do NOT include fake experience, fake publications, fake degrees, or fake skills.
- Keep the CV truthful and professional.
- Keep it formatted like a real CV.
- Use clear headings such as Profile, Education, Research Experience, Professional Experience, Technical Skills, Projects, Publications if available.
- If information is missing, simply omit it. Do not write "[Add link]" or "[Insert date]".
- Make the CV targeted to the opportunity but still realistic.

Opportunity:
Title: {opportunity.get("title")}
Organization: {opportunity.get("organization")}
Location: {opportunity.get("location")}
Requirements: {opportunity.get("requirements")}
Description: {opportunity.get("description")}
Eligibility: {opportunity.get("eligibility")}
Deadline: {opportunity.get("deadline")}
Link: {opportunity.get("link")}

Original CV:
{cv_text}

Now output ONLY the final refined CV:
"""

    try:
        response = generate_with_ollama(prompt)
        return clean_cv_output(response.strip())
    except Exception as error:
        return f"CV refinement failed. Error: {error}"


def clean_cv_output(text: str) -> str:
    bad_phrases = [
        "Here is a refined version",
        "I made the following changes",
        "Please note",
        "This is a refined version",
        "Now produce the refined CV"
    ]

    lines = text.splitlines()
    cleaned = []

    skip_section = False

    for line in lines:
        stripped = line.strip()

        if any(phrase.lower() in stripped.lower() for phrase in bad_phrases):
            skip_section = True
            continue

        if skip_section:
            # Stop skipping if a real CV heading appears again
            if stripped.lower() in [
                "profile", "research profile", "education",
                "research experience", "professional experience",
                "technical skills", "projects", "publications"
            ]:
                skip_section = False
            else:
                continue

        cleaned.append(line)

    return "\n".join(cleaned).strip()

def revise_cv_with_ollama(refined_cv: str, opportunity: dict, user_feedback: str) -> str:
    prompt = f"""
You are an expert academic CV revision assistant.

The user has reviewed a refined CV and provided feedback.
Revise the CV according to the feedback.

STRICT OUTPUT RULES:
- Output ONLY the revised CV content.
- Do NOT say "Here is the revised CV".
- Do NOT include "I made the following changes".
- Do NOT include notes, comments, explanations, placeholders, or warnings.
- Do NOT invent fake experience, fake degrees, fake publications, or fake skills.
- Keep the CV truthful and professional.
- Apply the user's feedback clearly.
- Keep the CV targeted to the opportunity.

Opportunity:
Title: {opportunity.get("title")}
Organization: {opportunity.get("organization")}
Location: {opportunity.get("location")}
Requirements: {opportunity.get("requirements")}
Description: {opportunity.get("description")}
Eligibility: {opportunity.get("eligibility")}

Current refined CV:
{refined_cv}

User feedback:
{user_feedback}

Now output ONLY the revised CV:
"""

    try:
        response = generate_with_ollama(prompt)
        return clean_cv_output(response.strip())
    except Exception as error:
        return f"CV revision failed. Error: {error}"
