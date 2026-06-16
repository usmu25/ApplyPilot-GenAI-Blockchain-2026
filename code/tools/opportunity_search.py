import os
from dotenv import load_dotenv
from tavily import TavilyClient

from tools.opportunity_parser import parse_opportunities_with_gemini


load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def build_base_query(intake_result: dict) -> str:
    opportunity_type = intake_result.get("opportunity_type", "General")
    field = intake_result.get("field", "")
    location = intake_result.get("location", "")

    if opportunity_type == "Academic":
        return f"{field} PhD position research assistantship {location} apply deadline"

    if opportunity_type == "Internship":
        return f"{field} internship {location} apply deadline"

    if opportunity_type == "Job":
        return f"{field} job {location} apply requirements"

    return f"{field} opportunity {location} apply"


def build_source_queries(intake_result: dict) -> list:
    base_query = build_base_query(intake_result)
    opportunity_type = intake_result.get("opportunity_type", "General")

    queries = [
        base_query,
        f"site:linkedin.com/jobs {base_query}",
        f"site:indeed.com {base_query}",
        f"site:glassdoor.com {base_query}",
        f"site:careers.* {base_query}",
    ]

    if opportunity_type == "Academic":
        queries.extend([
            f"site:academicpositions.com {base_query}",
            f"site:euraxess.ec.europa.eu {base_query}",
            f"site:jobs.ac.uk {base_query}",
            f"site:scholarshipdb.net {base_query}",
            f"site:findaphd.com {base_query}",
        ])

    return queries


def normalize_url(url: str) -> str:
    if not url:
        return ""

    return url.split("?")[0].rstrip("/")


def search_real_opportunities(intake_result: dict) -> list:
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY is missing in .env file")

    client = TavilyClient(api_key=TAVILY_API_KEY)

    queries = build_source_queries(intake_result)

    all_results = []
    seen_urls = set()

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=4
            )

            raw_results = response.get("results", [])

            for item in raw_results:
                url = normalize_url(item.get("url", ""))

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)
                all_results.append(item)

        except Exception as error:
            print(f"Search failed for query: {query}. Error: {error}")

    all_results = all_results[:15]

    parsed_opportunities = parse_opportunities_with_gemini(
        raw_results=all_results,
        intake_result=intake_result
    )

    return parsed_opportunities


def search_sample_opportunities(intake_result: dict) -> list:
    try:
        real_results = search_real_opportunities(intake_result)

        if real_results:
            return real_results

    except Exception as error:
        print(f"Real-time search failed. Using sample data. Error: {error}")

    fallback_opportunities = [
        {
            "title": "PhD Position in Computer Vision and Deep Learning",
            "organization": "Technical University of Munich",
            "type": "Academic",
            "field": "Computer Vision",
            "location": "Germany",
            "requirements": [
                "Python",
                "Machine Learning",
                "Computer Vision",
                "Research",
                "Image Processing"
            ],
            "description": "A research-focused PhD position involving deep learning methods for visual recognition and medical image analysis.",
            "deadline": "Not clearly mentioned",
            "eligibility": "Master degree preferred",
            "link": "https://example.com/phd-computer-vision-germany"
        },
        {
            "title": "Machine Learning Research Internship",
            "organization": "AI Research Lab",
            "type": "Internship",
            "field": "Machine Learning",
            "location": "Remote",
            "requirements": [
                "Python",
                "Machine Learning",
                "Data Analysis",
                "Research"
            ],
            "description": "A remote research internship focused on machine learning experiments, data analysis, and model evaluation.",
            "deadline": "Not clearly mentioned",
            "eligibility": "Students or recent graduates",
            "link": "https://example.com/ml-research-internship"
        },
        {
            "title": "AI Engineer Job",
            "organization": "VisionTech Solutions",
            "type": "Job",
            "field": "Artificial Intelligence",
            "location": "Germany",
            "requirements": [
                "Python",
                "Deep Learning",
                "Pytorch",
                "Computer Vision",
                "FastAPI"
            ],
            "description": "A full-time AI engineering role focused on building computer vision APIs and deploying machine learning models.",
            "deadline": "Not clearly mentioned",
            "eligibility": "Relevant AI or software engineering experience",
            "link": "https://example.com/ai-engineer-germany"
        }
    ]

    return fallback_opportunities
