def calculate_match_score(user_skills: list, requirements: list) -> int:
    if not requirements:
        return 0

    user_skills_lower = [skill.lower() for skill in user_skills]
    requirements_lower = [req.lower() for req in requirements]

    matched = []

    for requirement in requirements_lower:
        if requirement in user_skills_lower:
            matched.append(requirement)

    score = int((len(matched) / len(requirements_lower)) * 100)
    return score


def get_recommendation(score: int) -> str:
    if score >= 80:
        return "Strong Apply"
    elif score >= 60:
        return "Apply"
    elif score >= 40:
        return "Maybe Apply"
    else:
        return "Weak Match"


def analyze_opportunities(intake_result: dict, opportunities: list) -> list:
    user_skills = intake_result.get("skills_found", [])
    analyzed_results = []

    for opportunity in opportunities:
        requirements = opportunity.get("requirements", [])
        score = calculate_match_score(user_skills, requirements)

        matched_skills = []
        missing_skills = []

        user_skills_lower = [skill.lower() for skill in user_skills]

        for req in requirements:
            if req.lower() in user_skills_lower:
                matched_skills.append(req)
            else:
                missing_skills.append(req)

        analyzed_results.append({
            "title": opportunity.get("title"),
            "organization": opportunity.get("organization"),
            "type": opportunity.get("type"),
            "field": opportunity.get("field"),
            "location": opportunity.get("location"),
            "description": opportunity.get("description"),
            "requirements": requirements,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_score": score,
            "recommendation": get_recommendation(score),
            "link": opportunity.get("link")
        })

    analyzed_results.sort(key=lambda x: x["match_score"], reverse=True)

    return analyzed_results
