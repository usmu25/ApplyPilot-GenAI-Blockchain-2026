from tools.ollama_client import generate_with_ollama
import re


def clean_opportunity_title(title: str) -> str:
    if not title:
        return "the position"

    title = str(title).strip()

    # Remove category labels like [Jobs], [Job], [PhD], [Internship], [Scholarship]
    title = re.sub(r"^\s*\[[^\]]+\]\s*", "", title)

    # Remove trailing ellipsis from search result titles
    title = title.replace("...", "").replace("…", "")

    # Clean extra spaces
    title = " ".join(title.split())

    return title.strip() or "the position"

def clean_inline_markdown(text: str) -> str:
    if not text:
        return ""

    text = text.replace("**", "")
    text = text.replace("__", "")

    # Convert markdown links: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    return text.strip()


def infer_applicant_name(final_cv: str) -> str:
    """
    Try to extract applicant name from the CV.
    Falls back to 'Applicant' if no safe name is found.
    """
    if not final_cv:
        return "Applicant"

    skip_words = [
        "refined cv",
        "target opportunity",
        "contact information",
        "email",
        "phone",
        "linkedin",
        "orcid",
        "education",
        "research profile",
        "professional experience",
        "technical skills",
        "curriculum vitae",
        "cv"
    ]

    lines = final_cv.splitlines()

    for line in lines[:30]:
        clean_line = clean_inline_markdown(line)
        clean_line = clean_line.strip(":-•*# ").strip()

        if not clean_line:
            continue

        lower = clean_line.lower()

        if any(word in lower for word in skip_words):
            continue

        if "@" in clean_line or "http" in lower:
            continue

        if len(clean_line.split()) > 5:
            continue

        if len(clean_line) < 3:
            continue

        return clean_line

    return "Applicant"


def clean_cover_letter_text(text: str) -> str:
    """
    Cleans AI/meta wording, markdown artifacts, placeholders,
    and assistant-style text from cover letters.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Remove code fences if model returns them
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # If anything appears before the first 'Dear', remove it
    match = re.search(r"\bDear\b", text, flags=re.IGNORECASE)
    if match and match.start() > 0:
        text = text[match.start():].strip()

    # Remove common AI-style intro lines at beginning
    lines = text.split("\n")
    cleaned_lines = []

    skip_intro_phrases = [
        "here is",
        "here's",
        "below is",
        "sure",
        "certainly",
        "of course",
        "tailored cover letter",
        "cover letter for",
        "draft cover letter",
        "i have written",
        "i prepared"
    ]

    intro_phase = True

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if intro_phase and stripped:
            if any(phrase in lower for phrase in skip_intro_phrases) and not lower.startswith("dear "):
                continue
            intro_phase = False

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines).strip()

    # Remove markdown headings
    text = re.sub(r"^#+\s.*\n+", "", text, flags=re.MULTILINE)

    # Remove inline markdown
    text = clean_inline_markdown(text)

    # Remove placeholder lines
    placeholder_patterns = [
        r"\[add[^\]]*\]",
        r"\[insert[^\]]*\]",
        r"\[your[^\]]*\]",
        r"\[professor[^\]]*\]",
        r"\[university[^\]]*\]",
        r"\[name[^\]]*\]",
        r"\[email[^\]]*\]",
        r"\[link[^\]]*\]",
        r"add link",
        r"add links",
        r"insert here",
        r"replace this",
        r"placeholder",
        r"to be added",
        r"tbd"
    ]

    filtered_lines = []

    for line in text.split("\n"):
        line_lower = line.lower()
        has_placeholder = any(
            re.search(pattern, line_lower, flags=re.IGNORECASE)
            for pattern in placeholder_patterns
        )

        if not has_placeholder:
            filtered_lines.append(line)

    text = "\n".join(filtered_lines).strip()

    # Cut off assistant explanations after the real letter
    cutoff_phrases = [
        "I made the following changes",
        "Please note that",
        "This is a refined version",
        "You should replace",
        "Before final submission",
        "Let me know if",
        "I hope this helps",
        "Explanation:",
        "Changes made:"
    ]

    for phrase in cutoff_phrases:
        index = text.lower().find(phrase.lower())
        if index != -1:
            text = text[:index].strip()

    # Normalize extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_email_body_text(text: str) -> str:
    """
    Cleans email body from markdown, placeholders, and AI-style notes.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    text = clean_inline_markdown(text)

    # Remove assistant-style intro if present
    match = re.search(r"\bDear\b", text, flags=re.IGNORECASE)
    if match and match.start() > 0:
        text = text[match.start():].strip()

    # Remove placeholders
    text = re.sub(r"\[[^\]]*(add|insert|your|name|email|link|placeholder)[^\]]*\]", "", text, flags=re.IGNORECASE)

    # Normalize extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def generate_cover_letter(final_cv: str, opportunity: dict) -> str:
    applicant_name = infer_applicant_name(final_cv)

    prompt = f"""
You are an expert academic and professional application writer.

Write a tailored cover letter for this opportunity.

STRICT OUTPUT RULES:
- Output ONLY the final cover letter.
- Start directly with the salutation.
- Do not write "Here is a tailored cover letter".
- Do not write "Below is the cover letter".
- Do not include any explanation before or after the letter.
- Do not include email text.
- Do not use markdown headings.
- Do not use markdown bold text.
- Do not use bullet points.
- Do not use markdown links.
- Do not include placeholders such as [Add link], [Professor Name], [University], or [Your Name].
- If information is missing, omit it cleanly instead of inserting a placeholder.
- Do not invent experience, publications, supervisor names, dates, GPA, or links.
- Use only information supported by the finalized CV.
- Keep it professional, specific, and natural.
- Around 250-400 words.
- End with exactly:
Sincerely,
{applicant_name}

SALUTATION RULE:
- If a professor or specific contact name is clearly available in the opportunity, use it.
- Otherwise use: Dear Hiring Committee,

Opportunity:
Title: {clean_opportunity_title(opportunity.get("title", ""))}
Organization: {opportunity.get("organization", "")}
Location: {opportunity.get("location", "")}
Requirements: {opportunity.get("requirements", "")}
Description: {opportunity.get("description", "")}
Eligibility: {opportunity.get("eligibility", "")}

Finalized CV:
{final_cv}
"""

    raw_cover_letter = generate_with_ollama(prompt).strip()
    cleaned_cover_letter = clean_cover_letter_text(raw_cover_letter)

    # Final fallback if model forgot salutation
    if cleaned_cover_letter and not cleaned_cover_letter.lower().startswith("dear "):
        cleaned_cover_letter = "Dear Hiring Committee,\n\n" + cleaned_cover_letter

    # Final fallback if model forgot signature
    if "sincerely," not in cleaned_cover_letter.lower():
        cleaned_cover_letter = cleaned_cover_letter.rstrip() + f"\n\nSincerely,\n{applicant_name}"

    return cleaned_cover_letter.strip()


def generate_email_body(final_cv: str, opportunity: dict) -> str:
    applicant_name = infer_applicant_name(final_cv)

    title = clean_opportunity_title(opportunity.get("title", "the position"))
    organization = opportunity.get("organization", "your organization")

    email_body = f"""Dear Hiring Committee,

I hope you are doing well.

I am writing to apply for {title} at {organization}. Please find attached my CV and cover letter for your review.

Thank you for your time and consideration.

Best regards,
{applicant_name}"""

    return clean_email_body_text(email_body)


def generate_application_draft(final_cv: str, opportunity: dict) -> dict:
    cover_letter = generate_cover_letter(
        final_cv=final_cv,
        opportunity=opportunity
    )

    # Extra safety cleaning before saving draft
    cover_letter = clean_cover_letter_text(cover_letter)

    email_body = generate_email_body(
        final_cv=final_cv,
        opportunity=opportunity
    )

    title = clean_opportunity_title(opportunity.get("title", "Opportunity"))
    subject = f"Application for {title}"

    return {
        "subject": subject.strip(),
        "email_body": email_body.strip(),
        "cover_letter": cover_letter.strip()
    }


def generate_cover_letter_and_email(final_cv: str, opportunity: dict) -> str:
    """
    Kept for compatibility with older bot.py code.
    """
    draft = generate_application_draft(final_cv, opportunity)

    return (
        "Cover Letter:\n"
        + draft["cover_letter"]
        + "\n\nEmail Draft:\n"
        + "Subject: "
        + draft["subject"]
        + "\n\n"
        + draft["email_body"]
    )
