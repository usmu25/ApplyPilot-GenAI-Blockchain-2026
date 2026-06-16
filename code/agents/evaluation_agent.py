from datetime import datetime
import re


def detect_document_quality_issues(final_cv: str, cover_letter: str, email_body: str) -> dict:
    """
    Detect AI-draft, placeholder, formatting, and professionalism issues
    before application material is sent.
    """

    combined_text = "\n\n".join([
        final_cv or "",
        cover_letter or "",
        email_body or ""
    ])

    blocking_issues = []
    warnings = []

    # 1. Placeholder checks
    placeholder_patterns = [
        r"\[add[^\]]*\]",
        r"\[insert[^\]]*\]",
        r"\[your[^\]]*\]",
        r"\[email[^\]]*\]",
        r"\[link[^\]]*\]",
        r"add link",
        r"add links",
        r"insert here",
        r"replace this",
        r"placeholder",
        r"to be added",
        r"\btbd\b"
    ]

    for pattern in placeholder_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE):
            blocking_issues.append(
                f"Placeholder or unfinished text detected: {pattern}"
            )

    # 2. AI/meta output checks
    ai_meta_phrases = [
        "here is a tailored",
        "here is the tailored",
        "here is a refined",
        "here is the refined",
        "i made the following changes",
        "please note that this is",
        "this is a refined version",
        "you should replace",
        "before final submission",
        "as an ai",
        "i cannot",
        "i'm unable"
    ]

    lower_combined = combined_text.lower()

    for phrase in ai_meta_phrases:
        if phrase in lower_combined:
            blocking_issues.append(
                f"AI/meta draft phrase detected: {phrase}"
            )

    # 3. Markdown artifact checks
    markdown_patterns = [
        r"\[[^\]]+\]\([^)]+\)",        # markdown link
        r"mailto:",
        r"^#+\s+",                     # markdown heading
    ]

    for pattern in markdown_patterns:
        if re.search(pattern, combined_text, flags=re.IGNORECASE | re.MULTILINE):
            blocking_issues.append(
                f"Markdown formatting artifact detected: {pattern}"
            )

    # 4. Weak/generic salutation check for academic applications
    academic_terms = [
        "phd",
        "doctoral",
        "master",
        "ms",
        "professor",
        "lab",
        "research group",
        "scholarship"
    ]

    is_academic = any(term in lower_combined for term in academic_terms)

    if is_academic and re.search(r"dear hiring committee", cover_letter or "", flags=re.IGNORECASE):
        warnings.append(
            "Generic salutation detected. For academic applications, use professor/lab name when available."
        )

    # 5. Unsupported strong claim checks
    risky_claim_phrases = [
        "perfect fit",
        "guaranteed",
        "best candidate",
        "ideal candidate",
        "unmatched",
        "world-class",
        "expert in",
        "proven expertise in"
    ]

    for phrase in risky_claim_phrases:
        if phrase in lower_combined:
            warnings.append(
                f"Potentially exaggerated phrase detected: {phrase}"
            )

    # 6. Contact formatting checks
    if re.search(r"\[[^\]]*@[^]]+\]\(mailto:", final_cv or "", flags=re.IGNORECASE):
        blocking_issues.append(
            "Email appears as a markdown mailto link in the CV. It should be plain text."
        )

    if re.search(r"linkedin\s*/\s*orcid\s*:\s*\[", final_cv or "", flags=re.IGNORECASE):
        blocking_issues.append(
            "LinkedIn/ORCID placeholder detected in CV."
        )

    # 7. Cover letter should not start with assistant explanation
    first_300 = (cover_letter or "").strip()[:300].lower()

    bad_openings = [
        "here is",
        "below is",
        "sure",
        "certainly",
        "of course"
    ]

    for opening in bad_openings:
        if first_300.startswith(opening):
            blocking_issues.append(
                f"Cover letter starts with assistant-style wording: {opening}"
            )

    return {
        "blocking_issues": blocking_issues,
        "warnings": warnings
    }


def check_text_length(name: str, text: str, min_chars: int, max_chars: int = None) -> dict:
    length = len(text.strip()) if text else 0

    if length < min_chars:
        return {
            "name": name,
            "status": "fail",
            "message": f"{name} is too short. Length: {length} characters."
        }

    if max_chars and length > max_chars:
        return {
            "name": name,
            "status": "warning",
            "message": f"{name} is quite long. Length: {length} characters."
        }

    return {
        "name": name,
        "status": "pass",
        "message": f"{name} length is acceptable."
    }


def check_bad_cv_phrases(cv_text: str) -> list:
    if not cv_text:
        return []

    bad_phrases = [
        "here is a refined version",
        "i made the following changes",
        "please note",
        "replace placeholder",
        "[add link]",
        "[insert",
        "as an ai",
        "i cannot"
    ]

    issues = []
    lower_cv = cv_text.lower()

    for phrase in bad_phrases:
        if phrase in lower_cv:
            issues.append({
                "name": "CV unwanted phrase check",
                "status": "fail",
                "message": f"CV contains unwanted phrase: {phrase}"
            })

    return issues


def check_email_safety(email_body: str) -> list:
    if not email_body:
        return []

    issues = []
    risky_phrases = [
        "guaranteed",
        "urgent response required",
        "click here",
        "100%",
        "best candidate",
        "perfect fit"
    ]

    lower_body = email_body.lower()

    for phrase in risky_phrases:
        if phrase in lower_body:
            issues.append({
                "name": "Email safety check",
                "status": "warning",
                "message": f"Email contains potentially spammy phrase: {phrase}"
            })

    return issues


def evaluate_application_package(
    opportunity_number: str,
    opportunity: dict,
    final_cv: str,
    draft_data: dict
) -> dict:
    checks = []

    title = opportunity.get("title", "") if opportunity else ""
    organization = opportunity.get("organization", "") if opportunity else ""

    subject = draft_data.get("subject", "") if draft_data else ""
    email_body = draft_data.get("email_body", "") if draft_data else ""
    cover_letter = draft_data.get("cover_letter", "") if draft_data else ""

    # Basic length checks
    checks.append(check_text_length("Final CV", final_cv, min_chars=500, max_chars=9000))
    checks.append(check_text_length("Cover Letter", cover_letter, min_chars=500, max_chars=4000))
    checks.append(check_text_length("Email Body", email_body, min_chars=80, max_chars=1500))
    checks.append(check_text_length("Email Subject", subject, min_chars=8, max_chars=140))

    # Quality checks
    quality_check = detect_document_quality_issues(
        final_cv=final_cv,
        cover_letter=cover_letter,
        email_body=email_body
    )

    for issue in quality_check.get("blocking_issues", []):
        checks.append({
            "name": "Document quality check",
            "status": "fail",
            "message": issue
        })

    for warning in quality_check.get("warnings", []):
        checks.append({
            "name": "Document quality warning",
            "status": "warning",
            "message": warning
        })

    # CV phrase checks
    checks.extend(check_bad_cv_phrases(final_cv))

    # Email safety checks
    checks.extend(check_email_safety(email_body))

    # Opportunity checks
    if not title:
        checks.append({
            "name": "Opportunity title check",
            "status": "warning",
            "message": "Opportunity title is missing."
        })

    if not organization:
        checks.append({
            "name": "Organization check",
            "status": "warning",
            "message": "Organization name is missing."
        })

    # Attachment mention check
    if "attach" not in email_body.lower() and "attached" not in email_body.lower():
        checks.append({
            "name": "Attachment mention check",
            "status": "warning",
            "message": "Email body does not mention attachments."
        })

    fail_count = sum(1 for check in checks if check["status"] == "fail")
    warning_count = sum(1 for check in checks if check["status"] == "warning")
    pass_count = sum(1 for check in checks if check["status"] == "pass")

    if fail_count > 0:
        final_status = "FAILED"
    elif warning_count > 0:
        final_status = "NEEDS_REVIEW"
    else:
        final_status = "APPROVED"

    score = max(0, 100 - (fail_count * 25) - (warning_count * 8))

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "opportunity_number": opportunity_number,
        "opportunity_title": title,
        "organization": organization,
        "final_status": final_status,
        "score": score,
        "pass_count": pass_count,
        "warning_count": warning_count,
        "fail_count": fail_count,
        "checks": checks
    }


def format_evaluation_report(evaluation: dict) -> str:
    status = evaluation.get("final_status", "UNKNOWN")

    report = f"""
Evaluation Report

Opportunity:
{evaluation.get("opportunity_title")}

Organization:
{evaluation.get("organization")}

Status:
{status}

Score:
{evaluation.get("score")}/100

Summary:
Passed: {evaluation.get("pass_count")}
Warnings: {evaluation.get("warning_count")}
Failed: {evaluation.get("fail_count")}

Checks:
"""

    for check in evaluation.get("checks", []):
        icon = "✅" if check["status"] == "pass" else "⚠️" if check["status"] == "warning" else "❌"
        report += f"\n{icon} {check['name']}: {check['message']}"

    if status == "FAILED":
        report += "\n\nDecision: Do not send yet. Fix failed checks first."
    elif status == "NEEDS_REVIEW":
        report += "\n\nDecision: Review warnings before sending."
    elif status == "APPROVED":
        report += "\n\nDecision: Package is ready for sending."
    else:
        report += "\n\nDecision: Unknown status. Review manually."

    return report.strip()
