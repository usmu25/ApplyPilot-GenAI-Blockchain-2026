from agents.intake_agent import run_intake_agent
from agents.analysis_agent import analyze_opportunities
from agents.writer_agent import run_writer_agent
from tools.opportunity_search import search_sample_opportunities
from tools.logger import save_application_log


def run_applypilot_workflow(user_goal: str, cv_text: str) -> dict:
    intake_result = run_intake_agent(
        user_goal=user_goal,
        cv_text=cv_text
    )

    opportunities = search_sample_opportunities(intake_result)

    analyzed_opportunities = analyze_opportunities(
        intake_result=intake_result,
        opportunities=opportunities
    )

    selected_opportunity = analyzed_opportunities[0]

    writer_result = run_writer_agent(
        selected_opportunity=selected_opportunity,
        intake_result=intake_result,
        cv_text=cv_text
    )

    log_result = save_application_log(
        user_goal=user_goal,
        intake_result=intake_result,
        selected_opportunity=selected_opportunity,
        writer_result=writer_result
    )

    return {
        "user_goal": user_goal,
        "cv_received": True,

        "agent_1": "Intake Agent",
        "intake_result": intake_result,

        "agent_2": "Opportunity Search and Analysis Agent",
        "opportunities_found": len(opportunities),
        "analyzed_opportunities": analyzed_opportunities,

        "selected_opportunity": selected_opportunity,

        "agent_3": "Application Writer Agent",
        "writer_result": writer_result,

        "application_log": log_result
    }
def run_search_only_workflow(user_goal: str) -> dict:
    intake_result = run_intake_agent(
        user_goal=user_goal,
        cv_text=""
    )

    opportunities = search_sample_opportunities(intake_result)

    return {
        "user_goal": user_goal,
        "agent_1": "Search Intake Agent",
        "intake_result": intake_result,
        "agent_2": "Real-Time Search and Parser Agent",
        "opportunities_found": len(opportunities),
        "opportunities": opportunities
    }
