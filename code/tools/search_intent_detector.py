import re


ACADEMIC_KEYWORDS = [
    "phd",
    "ph.d",
    "ph.d.",
    "doctoral",
    "doctorate",
    "doctor",
    "ms",
    "m.s",
    "m.s.",
    "msc",
    "m.sc",
    "m.sc.",
    "master",
    "masters",
    "master's",
    "research assistant",
    "graduate assistant",
    "fully funded",
    "scholarship",
    "studentship",
    "professor",
    "supervisor",
    "lab",
    "research group",
    "graduate program",
    "graduate school"
]


def is_academic_search_query(query: str) -> bool:
    if not query:
        return False

    q = query.lower()

    for keyword in ACADEMIC_KEYWORDS:
        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

        if re.search(pattern, q):
            return True

    return False


def detect_degree_level(query: str) -> str:
    if not query:
        return "unknown"

    q = query.lower()

    phd_patterns = [
        r"\bphd\b",
        r"\bph\.d\.?\b",
        r"\bdoctoral\b",
        r"\bdoctorate\b"
    ]

    ms_patterns = [
        r"\bms\b",
        r"\bm\.s\.?\b",
        r"\bmsc\b",
        r"\bm\.sc\.?\b",
        r"\bmaster\b",
        r"\bmasters\b",
        r"\bmaster's\b"
    ]

    for pattern in phd_patterns:
        if re.search(pattern, q):
            return "PhD"

    for pattern in ms_patterns:
        if re.search(pattern, q):
            return "MS"

    return "academic"


def build_academic_search_query(user_query: str) -> str:
    return (
        f"{user_query} university lab professor research group "
        f"open position fully funded doctoral master scholarship "
        f"official department vacancy"
    )
