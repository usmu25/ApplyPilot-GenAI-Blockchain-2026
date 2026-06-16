def detect_opportunity_type(user_goal: str) -> str:
    goal = user_goal.lower()

    if "phd" in goal or "master" in goal or "professor" in goal or "research position" in goal:
        return "Academic"
    elif "internship" in goal or "intern" in goal:
        return "Internship"
    elif "job" in goal or "role" in goal or "position" in goal:
        return "Job"
    else:
        return "General"


def detect_location(user_goal: str) -> str:
    locations = [
        "germany", "usa", "uk", "canada", "australia", "china",
        "korea", "japan", "europe", "remote", "pakistan"
    ]

    goal = user_goal.lower()

    for location in locations:
        if location in goal:
            return location.title()

    return "Not specified"


def detect_field(user_goal: str) -> str:
    goal = user_goal.lower()

    fields = {
        "artificial intelligence": "Artificial Intelligence",
        "ai": "Artificial Intelligence",
        "machine learning": "Machine Learning",
        "computer vision": "Computer Vision",
        "data science": "Data Science",
        "robotics": "Robotics",
        "software": "Software Engineering",
        "seo": "SEO / Digital Marketing",
        "physics": "Physics",
        "optics": "Optics / Photonics",
        "biomedical": "Biomedical Engineering"
    }

    for keyword, field_name in fields.items():
        if keyword in goal:
            return field_name

    return "Not specified"


def extract_skills(cv_text: str) -> list:
    known_skills = [
        "python", "machine learning", "deep learning", "computer vision",
        "matlab", "research", "tensorflow", "pytorch", "seo",
        "google search console", "screaming frog", "shopify",
        "fastapi", "langgraph", "data analysis", "image processing"
    ]

    cv_lower = cv_text.lower()
    found_skills = []

    for skill in known_skills:
        if skill in cv_lower:
            found_skills.append(skill.title())

    return found_skills


def run_intake_agent(user_goal: str, cv_text: str) -> dict:
    return {
        "opportunity_type": detect_opportunity_type(user_goal),
        "field": detect_field(user_goal),
        "location": detect_location(user_goal),
        "skills_found": extract_skills(cv_text),
        "summary": "Intake Agent analyzed the user goal and CV text successfully."
    }
