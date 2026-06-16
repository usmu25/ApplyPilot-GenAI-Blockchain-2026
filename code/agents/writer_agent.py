from tools.gemini_client import generate_text


def clean_bullets(text: str) -> list:
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        line = line.lstrip("-•*0123456789. ")
        cleaned.append(line)

    return cleaned[:6]


def fallback_cv_suggestions(selected_opportunity: dict) -> list:
    matched_skills = selected_opportunity.get("matched_skills", [])
    missing_skills = selected_opportunity.get("missing_skills", [])

    suggestions = [
        "Move the most relevant skills near the top of the CV.",
        "Add 2-3 project or research bullets related to the selected opportunity.",
        "Use stronger action verbs and measurable outcomes where possible."
    ]

    if matched_skills:
        suggestions.append("Highlight matched skills: " + ", ".join(matched_skills))

    if missing_skills:
        suggestions.append("Address missing skills carefully in the cover letter: " + ", ".join(missing_skills))

    return suggestions


def generate_cv_suggestions(selected_opportunity: dict, intake_result: dict, cv_text: str) -> list:
    prompt = f"""
You are an expert CV advisor.

User profile:
{cv_text}

Opportunity:
Title: {selected_opportunity.get("title")}
Organization: {selected_opportunity.get("organization")}
Field: {selected_opportunity.get("field")}
Requirements: {selected_opportunity.get("requirements")}
Matched skills: {selected_opportunity.get("matched_skills")}
Missing skills: {selected_opportunity.get("missing_skills")}

Task:
Give 5 short, practical CV improvement suggestions.
Do not write a full CV.
Use bullet points only.
"""

    try:
        result = generate_text(prompt)
        suggestions = clean_bullets(result)
        return suggestions if suggestions else fallback_cv_suggestions(selected_opportunity)
    except Exception:
        return fallback_cv_suggestions(selected_opportunity)


def generate_cover_letter(selected_opportunity: dict, intake_result: dict, cv_text: str) -> str:
    prompt = f"""
You are an academic and professional application writing assistant.

Write a tailored cover letter for this opportunity.

please do not write any line like "Here is a tailored cover letter " avoid such words. 
Please do not write anything that makes no sense. please double check what you write.

User CV/profile:
{cv_text}

Opportunity:
Title: {selected_opportunity.get("title")}
Organization: {selected_opportunity.get("organization")}
Type: {selected_opportunity.get("type")}
Field: {selected_opportunity.get("field")}
Location: {selected_opportunity.get("location")}
Description: {selected_opportunity.get("description")}
Requirements: {selected_opportunity.get("requirements")}
Matched skills: {selected_opportunity.get("matched_skills")}
Missing skills: {selected_opportunity.get("missing_skills")}

Instructions:
- Do not include these phrases "Here is a tailored cover letter for the"
- Keep it professional.
- Keep it around 250-350 words.
- Do not exaggerate.
- Do not invent experience.
- Make it suitable for the selected opportunity.
- End with "Sincerely, Applicant".
"""

    try:
        return generate_text(prompt)
    except Exception:
        return f"""
Dear Hiring Committee,

I am writing to express my interest in the {selected_opportunity.get("title")} at {selected_opportunity.get("organization")}. My background and interests align with this opportunity, especially in the area of {selected_opportunity.get("field")}.

My experience includes {", ".join(selected_opportunity.get("matched_skills", []))}. I am also motivated to continue improving in areas required for this position.

Thank you for considering my application.

Sincerely,
Applicant
""".strip()


def generate_email_draft(selected_opportunity: dict, cover_letter: str) -> str:
    prompt = f"""
Write a short professional email to apply for this opportunity.
Please do not write anything that makes no sense. please double check what you write.
Opportunity:
Title: {selected_opportunity.get("title")}
Organization: {selected_opportunity.get("organization")}

Instructions:
- Include a clear subject line.
- Mention CV and cover letter are attached.
- Keep it concise.
- Do not use overly emotional language.
"""

    try:
        return generate_text(prompt)
    except Exception:
        return f"""
Subject: Application for {selected_opportunity.get("title")}

Dear Hiring Committee,

I hope you are doing well.

I am writing to apply for the {selected_opportunity.get("title")} at {selected_opportunity.get("organization")}. Please find attached my CV and cover letter for your review.

Thank you for your time and consideration.

Best regards,
Applicant
""".strip()


def run_writer_agent(selected_opportunity: dict, intake_result: dict, cv_text: str) -> dict:
    cv_suggestions = generate_cv_suggestions(
        selected_opportunity=selected_opportunity,
        intake_result=intake_result,
        cv_text=cv_text
    )

    cover_letter = generate_cover_letter(
        selected_opportunity=selected_opportunity,
        intake_result=intake_result,
        cv_text=cv_text
    )

    email_draft = generate_email_draft(
        selected_opportunity=selected_opportunity,
        cover_letter=cover_letter
    )

    return {
        "selected_opportunity": selected_opportunity.get("title"),
        "organization": selected_opportunity.get("organization"),
        "cv_suggestions": cv_suggestions,
        "cover_letter": cover_letter,
        "email_draft": email_draft,
        "summary": "Application Writer Agent generated AI-based CV suggestions, cover letter, and email draft."
    }
