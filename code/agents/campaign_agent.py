from agents.intake_agent import run_intake_agent
from agents.analysis_agent import analyze_opportunities
from agents.cv_refiner_agent import refine_cv_with_ollama
from tools.opportunity_search import search_sample_opportunities
from tools.agent_logger import create_session_id, log_agent_event


def create_cv_change_summary(opportunity: dict) -> list:
    requirements = opportunity.get("requirements", [])

    summary = [
        "CV draft prepared for this specific opportunity.",
        "Relevant skills and experience were prioritized.",
        "Unrelated details were reduced where possible."
    ]

    if requirements:
        summary.append(
            "Targeted requirements considered: " + ", ".join(requirements[:5])
        )

    return summary


def run_campaign_workflow(user_goal: str, cv_text: str, top_n: int = 3, session_id: str = None) -> dict:
    if not session_id:
        session_id = create_session_id("campaign")

    log_agent_event(
        session_id=session_id,
        agent_name="Campaign Manager",
        action="campaign_started",
        input_data={
            "user_goal": user_goal,
            "cv_length": len(cv_text)
        }
    )

    try:
        intake_result = run_intake_agent(
            user_goal=user_goal,
            cv_text=cv_text
        )

        log_agent_event(
            session_id=session_id,
            agent_name="Intake Agent",
            action="analyze_user_goal_and_cv",
            input_data={
                "user_goal": user_goal,
                "cv_length": len(cv_text)
            },
            output_data=intake_result
        )

    except Exception as error:
        log_agent_event(
            session_id=session_id,
            agent_name="Intake Agent",
            action="analyze_user_goal_and_cv",
            status="failed",
            error=error
        )
        raise error

    try:
        opportunities = search_sample_opportunities(intake_result)

        log_agent_event(
            session_id=session_id,
            agent_name="Search Agent",
            action="real_time_opportunity_search",
            input_data=intake_result,
            output_data={
                "opportunities_found": len(opportunities),
                "opportunities": opportunities
            }
        )

    except Exception as error:
        log_agent_event(
            session_id=session_id,
            agent_name="Search Agent",
            action="real_time_opportunity_search",
            status="failed",
            error=error
        )
        raise error

    try:
        analyzed_opportunities = analyze_opportunities(
            intake_result=intake_result,
            opportunities=opportunities
        )

        top_opportunities = analyzed_opportunities[:top_n]

        log_agent_event(
            session_id=session_id,
            agent_name="Ranking Agent",
            action="rank_and_shortlist_opportunities",
            input_data={
                "total_opportunities": len(opportunities),
                "top_n": top_n
            },
            output_data={
                "top_opportunities": top_opportunities
            }
        )

    except Exception as error:
        log_agent_event(
            session_id=session_id,
            agent_name="Ranking Agent",
            action="rank_and_shortlist_opportunities",
            status="failed",
            error=error
        )
        raise error

    cv_drafts = []

    for index, opportunity in enumerate(top_opportunities, start=1):
        try:
            refined_cv = refine_cv_with_ollama(
                cv_text=cv_text,
                opportunity=opportunity
            )

            draft = {
                "campaign_number": index,
                "opportunity": opportunity,
                "refined_cv": refined_cv,
                "cv_change_summary": create_cv_change_summary(opportunity),
                "status": "draft"
            }

            cv_drafts.append(draft)

            log_agent_event(
                session_id=session_id,
                agent_name="CV Tailoring Agent",
                action=f"refine_cv_for_opportunity_{index}",
                input_data={
                    "opportunity": opportunity,
                    "cv_length": len(cv_text)
                },
                output_data={
                    "campaign_number": index,
                    "opportunity_title": opportunity.get("title"),
                    "refined_cv": refined_cv,
                    "cv_change_summary": draft["cv_change_summary"]
                }
            )

        except Exception as error:
            log_agent_event(
                session_id=session_id,
                agent_name="CV Tailoring Agent",
                action=f"refine_cv_for_opportunity_{index}",
                status="failed",
                input_data={
                    "opportunity": opportunity
                },
                error=error
            )

    result = {
        "session_id": session_id,
        "user_goal": user_goal,
        "intake_result": intake_result,
        "opportunities_found": len(opportunities),
        "analyzed_opportunities": analyzed_opportunities,
        "top_opportunities": top_opportunities,
        "cv_drafts": cv_drafts,
        "status": "campaign_drafts_ready"
    }

    log_agent_event(
        session_id=session_id,
        agent_name="Campaign Manager",
        action="campaign_completed",
        output_data={
            "session_id": session_id,
            "opportunities_found": len(opportunities),
            "cv_drafts_created": len(cv_drafts)
        }
    )

    return result

