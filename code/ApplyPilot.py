import os
from dotenv import load_dotenv

from tools.activity_logger import log_telegram_event, log_agent_action

import asyncio
from agents.evaluation_agent import evaluate_application_package, format_evaluation_report
from tools.email_sender import send_email_with_attachments
from tools.email_tracker import check_replies_and_update_tracker
from tools.application_tracker import (
    generate_application_id,
    log_email_sent,
    format_status_rows
)
from tools.document_exporter import (
    save_cv_as_pdf,
    save_cover_letter_as_pdf
)
from agents.campaign_agent import run_campaign_workflow
from tools.agent_logger import create_session_id, log_agent_event
from agents.cv_refiner_agent import refine_cv_with_ollama, revise_cv_with_ollama
from agents.draft_agent import generate_application_draft
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from workflow import run_applypilot_workflow, run_search_only_workflow
from tools.cv_reader import extract_cv_text
from agents.chat_agent import run_chat_agent

from agents.chat_agent import run_chat_agent
from tools.search_intent_detector import (
    is_academic_search_query,
    detect_degree_level,
    build_academic_search_query
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WAITING_GOAL, WAITING_CV, WAITING_SEARCH_KEYWORDS, WAITING_REFINE_CV, WAITING_REVISE_CV, WAITING_CAMPAIGN_CV, WAITING_CAMPAIGN_GOAL = range(7)

def split_message(text: str, limit: int = 3500) -> list:
    return [text[i:i + limit] for i in range(0, len(text), limit)]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_notify_chat_id(update.effective_chat.id)
    message = """
Welcome to ApplyPilot.

You can use me in two ways:

1. Normal chat
Just send any message like:
How are you?
How is the weather in Seoul?

2. Opportunity search
Send /apply to start job, internship, or PhD opportunity search.

ApplyPilot can:
- Read your CV
- Search real-time opportunities
- Analyze your fit
- Generate CV suggestions
- Write a cover letter
- Draft an application email
- Save the application log
"""
    await update.message.reply_text(message.strip())


async def apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please enter your goal.\n\n"
        "Example:\nFind PhD positions in computer vision in Germany"
    )
    return WAITING_GOAL


async def receive_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_goal"] = update.message.text

    await update.message.reply_text(
        "Great. Now upload your CV as PDF/DOCX/TXT, or paste your CV text here."
    )
    return WAITING_CV


async def send_applypilot_result(update: Update, user_goal: str, cv_text: str):
    await update.message.reply_text("ApplyPilot agents are working. Please wait...")

    result = run_applypilot_workflow(
        user_goal=user_goal,
        cv_text=cv_text
    )

    intake = result["intake_result"]
    selected = result["selected_opportunity"]
    writer = result["writer_result"]

    skills_text = ", ".join(intake["skills_found"]) if intake["skills_found"] else "No skills detected"

    opportunities_text = ""

    for index, opportunity in enumerate(result["analyzed_opportunities"][:3], start=1):
        opportunities_text += f"""
{index}. {opportunity["title"]}
Organization: {opportunity["organization"]}
Location: {opportunity["location"]}
Score: {opportunity["match_score"]}%
Deadline: {opportunity.get("deadline", "Not clearly mentioned")}
Link: {opportunity["link"]}

"""

    summary = f"""
ApplyPilot Result

Goal:
{result["user_goal"]}

Intake Agent:
Type: {intake["opportunity_type"]}
Field: {intake["field"]}
Location: {intake["location"]}
Skills Found: {skills_text}

Top Real-Time Opportunities:
{opportunities_text}

Best Matched Opportunity:
Title: {selected["title"]}
Organization: {selected["organization"]}
Location: {selected["location"]}
Match Score: {selected["match_score"]}%
Recommendation: {selected["recommendation"]}

Application Log:
{result["application_log"]["status"]} in {result["application_log"]["file"]}
"""

    for part in split_message(summary.strip()):
        await update.message.reply_text(part)

    cv_suggestions = "CV Suggestions:\n\n" + "\n".join(
        [f"- {item}" for item in writer["cv_suggestions"]]
    )

    await update.message.reply_text(cv_suggestions)

    cover_letter = "Cover Letter:\n\n" + writer["cover_letter"]

    for part in split_message(cover_letter):
        await update.message.reply_text(part)

    email_draft = "Email Draft:\n\n" + writer["email_draft"]

    for part in split_message(email_draft):
        await update.message.reply_text(part)


async def receive_cv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_goal = context.user_data.get("user_goal")
    cv_text = update.message.text

    await send_applypilot_result(update, user_goal, cv_text)

    return ConversationHandler.END


async def receive_cv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_goal = context.user_data.get("user_goal")
    document = update.message.document

    file_name = document.file_name or "uploaded_cv"
    extension = os.path.splitext(file_name)[1].lower()

    if extension not in [".pdf", ".docx", ".txt"]:
        await update.message.reply_text(
            "Unsupported file type. Please upload PDF, DOCX, or TXT."
        )
        return WAITING_CV

    os.makedirs("data/uploads", exist_ok=True)

    saved_path = f"data/uploads/{document.file_unique_id}_{file_name}"

    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(saved_path)

    try:
        cv_text = extract_cv_text(saved_path)
    except Exception as error:
        await update.message.reply_text(f"Could not read the CV file. Error: {error}")
        return WAITING_CV

    if not cv_text or len(cv_text.strip()) < 30:
        await update.message.reply_text(
            "I could not extract enough text from this CV. "
            "Please upload a text-based PDF/DOCX or paste your CV text."
        )
        return WAITING_CV

    await update.message.reply_text("CV uploaded and read successfully.")

    await send_applypilot_result(update, user_goal, cv_text)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Application process cancelled.")
    return ConversationHandler.END


async def normal_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    await update.message.reply_text("Thinking...")

    response = run_chat_agent(user_message)

    for part in split_message(response):
        await update.message.reply_text(part)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Enter your search keywords or goal.\n\n"
        "Examples:\n"
        "Computer vision PhD Germany\n"
        "AI internship remote\n"
        "Machine learning jobs Canada"
    )
    return WAITING_SEARCH_KEYWORDS


async def receive_search_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_goal = update.message.text.strip()

    log_agent_action(
        agent="Search Agent",
        action="search_started",
        outcome="OK",
        notes=f"Search query received: {user_goal}"
    )

    academic_mode = is_academic_search_query(user_goal)
    degree_level = detect_degree_level(user_goal)

    if academic_mode:
        search_goal = build_academic_search_query(user_goal)

        await update.message.reply_text(
            f"Academic search mode detected.\n\n"
            f"Degree level: {degree_level}\n"
            f"I will prioritize universities, labs, professors, and official academic position pages."
        )
    else:
        search_goal = user_goal

        await update.message.reply_text(
            "General opportunity search mode detected."
        )

    await update.message.reply_text(
        "Searching real-time opportunities from web, LinkedIn, Indeed, and academic sources. Please wait..."
    )

    result = run_search_only_workflow(search_goal)
    log_agent_action(
    agent="Search Agent",
    action="search_completed",
    outcome="OK",
    notes="Search workflow completed"
    )

    opportunities = result["opportunities"]

    if not opportunities:
        await update.message.reply_text(
            "No opportunities found. Try broader keywords."
        )
        return ConversationHandler.END

    response = f"""
Search Results

Goal:
{result["user_goal"]}

Opportunities Found:
{result["opportunities_found"]}

Reply later with numbers when we add shortlisting.
Example: 1 3 5

Top Opportunities:
"""

    for index, opportunity in enumerate(opportunities[:10], start=1):
        response += f"""
{index}. {opportunity.get("title", "Untitled")}
Organization: {opportunity.get("organization", "Not clearly detected")}
Location: {opportunity.get("location", "Not clearly mentioned")}
Deadline: {opportunity.get("deadline", "Not clearly mentioned")}
Link: {opportunity.get("link", "")}

"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

    context.user_data["last_search_results"] = opportunities

    return ConversationHandler.END

async def select_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opportunities = context.user_data.get("last_search_results", [])

    if not opportunities:
        await update.message.reply_text(
            "No search results found. Please use /search first."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please select opportunity numbers.\n\nExample:\n/select 1 3 5"
        )
        return

    selected = []
    invalid_numbers = []

    for arg in context.args:
        try:
            number = int(arg)
            if 1 <= number <= len(opportunities):
                selected.append({
                    "original_number": number,
                    "opportunity": opportunities[number - 1]
                })
            else:
                invalid_numbers.append(arg)
        except ValueError:
            invalid_numbers.append(arg)

    if not selected:
        await update.message.reply_text(
            "No valid opportunity numbers selected. Example:\n/select 1 3"
        )
        return

    context.user_data["shortlisted_opportunities"] = selected

    response = "Shortlisted Opportunities:\n\n"

    for item in selected:
        opportunity = item["opportunity"]
        response += f"""
{item["original_number"]}. {opportunity.get("title", "Untitled")}
Organization: {opportunity.get("organization", "Not clearly detected")}
Location: {opportunity.get("location", "Not clearly mentioned")}
Link: {opportunity.get("link", "")}

"""

    response += "Next, use /refinecv with the original opportunity number.\nExample:\n/refinecv 1"

    if invalid_numbers:
        response += f"\n\nInvalid numbers ignored: {', '.join(invalid_numbers)}"

    for part in split_message(response.strip()):
        await update.message.reply_text(part)


async def refinecv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shortlisted = context.user_data.get("shortlisted_opportunities", [])

    if not shortlisted:
        await update.message.reply_text(
            "No shortlisted opportunities found. Please use /search and then /select first."
        )
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text(
            "Please choose one shortlisted opportunity number.\n\nExample:\n/refinecv 1"
        )
        return ConversationHandler.END

    try:
        requested_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Please use a valid number.\n\nExample:\n/refinecv 1"
        )
        return ConversationHandler.END

    selected_item = None

    for item in shortlisted:
        if item["original_number"] == requested_number:
            selected_item = item
            break

    if not selected_item:
        await update.message.reply_text(
            "This opportunity is not in your shortlist. Please use one of your shortlisted numbers."
        )
        return ConversationHandler.END

    context.user_data["refine_opportunity_number"] = requested_number
    context.user_data["refine_opportunity"] = selected_item["opportunity"]

    opportunity = selected_item["opportunity"]

    await update.message.reply_text(
        f"You selected:\n{opportunity.get('title')}\n\n"
        "Now upload your CV as PDF/DOCX/TXT, or paste your CV text here. "
        "I will refine it for this opportunity using Ollama."
    )

    return WAITING_REFINE_CV

async def receive_refine_cv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cv_text = update.message.text
    opportunity = context.user_data.get("refine_opportunity")
    opportunity_number = context.user_data.get("refine_opportunity_number")

    if not opportunity:
        await update.message.reply_text(
            "No opportunity selected. Please use /refinecv again."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Ollama is refining your CV for this opportunity. Please wait..."
    )

    refined_cv = refine_cv_with_ollama(
        cv_text=cv_text,
        opportunity=opportunity
    )

    if "refined_cv_versions" not in context.user_data:
        context.user_data["refined_cv_versions"] = {}

    context.user_data["refined_cv_versions"][str(opportunity_number)] = {
        "opportunity": opportunity,
        "refined_cv": refined_cv,
        "status": "draft"
    }

    response = f"""
Refined CV Draft for Opportunity {opportunity_number}

Opportunity:
{opportunity.get("title")}

Please review this CV.

After review, the next step will be:
/revisecv {opportunity_number}

Refined CV:
{refined_cv}
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

    return ConversationHandler.END

async def receive_refine_cv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    opportunity = context.user_data.get("refine_opportunity")
    opportunity_number = context.user_data.get("refine_opportunity_number")

    if not opportunity:
        await update.message.reply_text(
            "No opportunity selected. Please use /refinecv again."
        )
        return ConversationHandler.END

    file_name = document.file_name or "uploaded_cv"
    extension = os.path.splitext(file_name)[1].lower()

    if extension not in [".pdf", ".docx", ".txt"]:
        await update.message.reply_text(
            "Unsupported file type. Please upload PDF, DOCX, or TXT."
        )
        return WAITING_REFINE_CV

    os.makedirs("data/uploads", exist_ok=True)

    saved_path = f"data/uploads/refine_{document.file_unique_id}_{file_name}"

    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(saved_path)

    try:
        cv_text = extract_cv_text(saved_path)
    except Exception as error:
        await update.message.reply_text(f"Could not read the CV file. Error: {error}")
        return WAITING_REFINE_CV

    if not cv_text or len(cv_text.strip()) < 30:
        await update.message.reply_text(
            "I could not extract enough text from this CV. "
            "Please upload a text-based PDF/DOCX or paste your CV text."
        )
        return WAITING_REFINE_CV

    await update.message.reply_text(
        "CV uploaded and read successfully. Ollama is refining it now. Please wait..."
    )

    refined_cv = refine_cv_with_ollama(
        cv_text=cv_text,
        opportunity=opportunity
    )

    if "refined_cv_versions" not in context.user_data:
        context.user_data["refined_cv_versions"] = {}

    context.user_data["refined_cv_versions"][str(opportunity_number)] = {
        "opportunity": opportunity,
        "original_cv_file": saved_path,
        "original_cv_text": cv_text,
        "refined_cv": refined_cv,
        "status": "draft"
    }

    response = f"""
Refined CV Draft for Opportunity {opportunity_number}

Opportunity:
{opportunity.get("title")}

Please review this CV.

After review, the next step will be:
/revisecv {opportunity_number}

Refined CV:
{refined_cv}
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

    return ConversationHandler.END

async def revisecv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refined_versions = context.user_data.get("refined_cv_versions", {})

    if not refined_versions:
        await update.message.reply_text(
            "No refined CV found. Please use /refinecv first."
        )
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text(
            "Please choose a refined CV number.\n\nExample:\n/revisecv 1"
        )
        return ConversationHandler.END

    opportunity_number = context.args[0]

    if opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No refined CV found for this opportunity number."
        )
        return ConversationHandler.END

    context.user_data["revise_opportunity_number"] = opportunity_number

    await update.message.reply_text(
        "Please send your revision feedback.\n\n"
        "Example:\nMake the research experience stronger and reduce the teaching part."
    )

    return WAITING_REVISE_CV


async def receive_revise_cv_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedback = update.message.text
    opportunity_number = context.user_data.get("revise_opportunity_number")

    refined_versions = context.user_data.get("refined_cv_versions", {})

    if not opportunity_number or opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No CV revision session found. Please use /revisecv again."
        )
        return ConversationHandler.END

    current_data = refined_versions[opportunity_number]

    opportunity = current_data["opportunity"]
    current_cv = current_data["refined_cv"]

    await update.message.reply_text(
        "Ollama is revising your CV based on your feedback. Please wait..."
    )

    revised_cv = revise_cv_with_ollama(
        refined_cv=current_cv,
        opportunity=opportunity,
        user_feedback=feedback
    )

    current_data["refined_cv"] = revised_cv
    current_data["status"] = "revised"
    current_data["last_feedback"] = feedback

    context.user_data["refined_cv_versions"][opportunity_number] = current_data

    response = f"""
Revised CV for Opportunity {opportunity_number}

Opportunity:
{opportunity.get("title")}

Status:
Revised draft

Next options:
- Send /revisecv {opportunity_number} again if you want more changes
- Send /finalizecv {opportunity_number} when this version is final

Revised CV:
{revised_cv}
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

    return ConversationHandler.END


async def finalizecv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refined_versions = context.user_data.get("refined_cv_versions", {})

    if not refined_versions:
        await update.message.reply_text(
            "No refined CV found. Please use /refinecv first."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please choose a CV number to finalize.\n\nExample:\n/finalizecv 1"
        )
        return

    opportunity_number = context.args[0]

    if opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No refined CV found for this opportunity number."
        )
        return

    refined_versions[opportunity_number]["status"] = "finalized"
    context.user_data["refined_cv_versions"] = refined_versions

    opportunity = refined_versions[opportunity_number]["opportunity"]

    await update.message.reply_text(
        f"Final CV saved for Opportunity {opportunity_number}.\n\n"
        f"Opportunity:\n{opportunity.get('title')}\n\n"
        f"When you want cover letter and email draft, use:\n/draft {opportunity_number}"
    )


async def draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refined_versions = context.user_data.get("refined_cv_versions", {})

    if not refined_versions:
        await update.message.reply_text(
            "No refined CV found. Please use /refinecv or /campaign first."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please choose a finalized CV number.\n\nExample:\n/draft 1"
        )
        return

    opportunity_number = context.args[0]

    if opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No CV found for this opportunity number."
        )
        return

    cv_data = refined_versions[opportunity_number]

    if cv_data.get("status") != "finalized":
        await update.message.reply_text(
            f"This CV is not finalized yet.\n\nPlease finalize it first:\n/finalizecv {opportunity_number}"
        )
        return

    opportunity = cv_data["opportunity"]
    final_cv = cv_data["refined_cv"]

    await update.message.reply_text(
        "Generating cover letter and email draft using your finalized CV. Please wait..."
    )

    try:
        draft_result = generate_application_draft(
            final_cv=final_cv,
            opportunity=opportunity
        )
    except Exception as error:
        await update.message.reply_text(
            f"Draft generation failed.\n\nError:\n{error}"
        )
        return

    if "application_drafts" not in context.user_data:
        context.user_data["application_drafts"] = {}

    context.user_data["application_drafts"][opportunity_number] = {
        "opportunity": opportunity,
        "final_cv": final_cv,
        "draft": draft_result,
        "status": "drafted"
    }
    log_agent_action(
    agent="Draft Agent",
    action="draft_generated",
    outcome="OK",
    notes=f"Draft generated for opportunity {opportunity_number}"
    )
    response = f"""
Application Draft for Opportunity {opportunity_number}

Opportunity:
{opportunity.get("title")}

Organization:
{opportunity.get("organization")}

Subject:
{draft_result["subject"]}

Email Body:
{draft_result["email_body"]}

Cover Letter:
{draft_result["cover_letter"]}

Status:
Draft created. Please review before sending.
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

async def campaign_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = create_session_id("campaign")
    context.user_data["campaign_session_id"] = session_id

    log_agent_event(
        session_id=session_id,
        agent_name="Telegram Bot",
        action="campaign_command_started",
        input_data={
            "telegram_user": update.effective_user.id if update.effective_user else None
        }
    )

    await update.message.reply_text(
        "ApplyPilot Campaign Mode started.\n\n"
        "Step 1: Upload your CV as PDF/DOCX/TXT, or paste your CV text here.\n\n"
        "I will use this CV once and prepare tailored drafts for the top opportunities."
    )

    return WAITING_CAMPAIGN_CV


async def receive_campaign_cv_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cv_text = update.message.text
    session_id = context.user_data.get("campaign_session_id")

    context.user_data["campaign_cv_text"] = cv_text
    context.user_data["campaign_cv_source"] = "text"

    log_agent_event(
        session_id=session_id,
        agent_name="Telegram Bot",
        action="campaign_cv_received_text",
        input_data={
            "cv_length": len(cv_text)
        }
    )

    await update.message.reply_text(
        "CV received.\n\n"
        "Step 2: Enter your search goal or keywords.\n\n"
        "Example:\nComputer vision PhD Germany"
    )

    return WAITING_CAMPAIGN_GOAL


async def receive_campaign_cv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = context.user_data.get("campaign_session_id")
    document = update.message.document

    file_name = document.file_name or "uploaded_cv"
    extension = os.path.splitext(file_name)[1].lower()

    if extension not in [".pdf", ".docx", ".txt"]:
        await update.message.reply_text(
            "Unsupported file type. Please upload PDF, DOCX, or TXT."
        )
        return WAITING_CAMPAIGN_CV

    os.makedirs("data/uploads", exist_ok=True)

    saved_path = f"data/uploads/campaign_{document.file_unique_id}_{file_name}"

    telegram_file = await document.get_file()
    await telegram_file.download_to_drive(saved_path)

    try:
        cv_text = extract_cv_text(saved_path)
    except Exception as error:
        log_agent_event(
            session_id=session_id,
            agent_name="CV Reader Tool",
            action="extract_campaign_cv_text",
            status="failed",
            input_data={
                "file_name": file_name,
                "saved_path": saved_path
            },
            error=error
        )

        await update.message.reply_text(f"Could not read the CV file. Error: {error}")
        return WAITING_CAMPAIGN_CV

    if not cv_text or len(cv_text.strip()) < 30:
        await update.message.reply_text(
            "I could not extract enough text from this CV. "
            "Please upload a text-based PDF/DOCX or paste your CV text."
        )
        return WAITING_CAMPAIGN_CV

    context.user_data["campaign_cv_text"] = cv_text
    context.user_data["campaign_cv_source"] = saved_path

    log_agent_event(
        session_id=session_id,
        agent_name="CV Reader Tool",
        action="extract_campaign_cv_text",
        input_data={
            "file_name": file_name,
            "saved_path": saved_path
        },
        output_data={
            "cv_length": len(cv_text)
        }
    )

    await update.message.reply_text(
        "CV uploaded and read successfully.\n\n"
        "Step 2: Enter your search goal or keywords.\n\n"
        "Example:\nComputer vision PhD Germany"
    )

    return WAITING_CAMPAIGN_GOAL


async def receive_campaign_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_goal = update.message.text.strip()
    session_id = context.user_data.get("campaign_session_id")
    cv_text = context.user_data.get("campaign_cv_text")

    academic_mode = is_academic_search_query(user_goal)
    degree_level = detect_degree_level(user_goal)
    log_agent_action(
    agent="Campaign Agent",
    action="campaign_goal_received",
    outcome="OK",
    notes=f"Goal: {user_goal}; academic_mode={academic_mode}; degree={degree_level}"
    )
    if academic_mode:
        search_goal = build_academic_search_query(user_goal)

        await update.message.reply_text(
            f"Academic search mode detected.\n\n"
            f"Degree level: {degree_level}\n"
            f"I will prioritize universities, labs, professors, and official academic position pages."
        )
    else:
        search_goal = user_goal

        await update.message.reply_text(
            "General opportunity search mode detected."
        )
    if not cv_text:
        await update.message.reply_text(
            "No CV found in this campaign session. Please start again with /campaign."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Campaign agents are working now.\n\n"
        "This may take some time because I am:\n"
        "1. Searching real-time opportunities\n"
        "2. Ranking the best matches\n"
        "3. Preparing tailored CV drafts for the top opportunities"
    )

    try:
        campaign_result = run_campaign_workflow(
            user_goal=search_goal,
            cv_text=cv_text,
            top_n=3,
            session_id=session_id
        )

    except Exception as error:
        log_agent_event(
            session_id=session_id,
            agent_name="Campaign Manager",
            action="run_campaign_workflow",
            status="failed",
            error=error
        )

        await update.message.reply_text(
            f"Campaign failed. Error: {error}"
        )
        return ConversationHandler.END
    log_agent_action(
    agent="Campaign Agent",
    action="campaign_completed",
    outcome="OK",
    notes="Campaign search, ranking, and CV drafts completed"
    )
    context.user_data["campaign_result"] = campaign_result

    if "refined_cv_versions" not in context.user_data:
        context.user_data["refined_cv_versions"] = {}

    for draft in campaign_result["cv_drafts"]:
        number = str(draft["campaign_number"])
        context.user_data["refined_cv_versions"][number] = {
            "opportunity": draft["opportunity"],
            "refined_cv": draft["refined_cv"],
            "status": "draft",
            "source": "campaign",
            "session_id": session_id
        }

    response = f"""
Campaign Results

Session ID:
{campaign_result["session_id"]}

Goal:
{campaign_result["user_goal"]}

Opportunities Found:
{campaign_result["opportunities_found"]}

Top Prepared Opportunities:
"""

    for draft in campaign_result["cv_drafts"]:
        opportunity = draft["opportunity"]

        response += f"""
{draft["campaign_number"]}. {opportunity.get("title", "Untitled")}
Organization: {opportunity.get("organization", "Not clearly detected")}
Location: {opportunity.get("location", "Not clearly mentioned")}
Match Score: {opportunity.get("match_score", "N/A")}%
Recommendation: {opportunity.get("recommendation", "N/A")}
Deadline: {opportunity.get("deadline", "Not clearly mentioned")}
Link: {opportunity.get("link", "")}

CV Changes Prepared:
- {draft["cv_change_summary"][0]}
- {draft["cv_change_summary"][1]}
- {draft["cv_change_summary"][2]}

"""

    response += """
Next options:
- /showcampaigncv 1
- /revisecv 1
- /finalizecv 1
- /draft 1

Logs saved in:
data/logs/agent_activity.jsonl
data/logs/sessions/
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

    return ConversationHandler.END


async def showcampaigncv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    campaign_result = context.user_data.get("campaign_result")

    if not campaign_result:
        await update.message.reply_text(
            "No campaign result found. Please run /campaign first."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please choose a campaign CV number.\n\nExample:\n/showcampaigncv 1"
        )
        return

    number = context.args[0]

    selected_draft = None

    for draft in campaign_result.get("cv_drafts", []):
        if str(draft["campaign_number"]) == str(number):
            selected_draft = draft
            break

    if not selected_draft:
        await update.message.reply_text(
            "No CV draft found for this number."
        )
        return

    session_id = campaign_result.get("session_id")

    log_agent_event(
        session_id=session_id,
        agent_name="Telegram Bot",
        action="show_campaign_cv",
        input_data={
            "campaign_number": number
        }
    )

    opportunity = selected_draft["opportunity"]
    refined_cv = selected_draft["refined_cv"]

    response = f"""
Campaign CV Draft {number}

Opportunity:
{opportunity.get("title")}

Refined CV:
{refined_cv}
"""

    for part in split_message(response.strip()):
        await update.message.reply_text(part)

async def sendemail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refined_versions = context.user_data.get("refined_cv_versions", {})
    application_drafts = context.user_data.get("application_drafts", {})

    if len(context.args) < 2:
        await update.message.reply_text(
            "Use this format:\n/sendemail 1 receiver@email.com"
        )
        return

    opportunity_number = context.args[0]
    recipient_email = context.args[1]

    if opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No finalized CV found for this opportunity. Please use /finalizecv first."
        )
        return

    cv_data = refined_versions[opportunity_number]

    if cv_data.get("status") != "finalized":
        await update.message.reply_text(
            f"This CV is not finalized yet. Use:\n/finalizecv {opportunity_number}"
        )
        return

    if opportunity_number not in application_drafts:
        await update.message.reply_text(
            f"No email draft found for this opportunity. Please use:\n/draft {opportunity_number}"
        )
        return

    opportunity = cv_data["opportunity"]
    final_cv = cv_data["refined_cv"]
    draft_data = application_drafts[opportunity_number]["draft"]

    if not isinstance(draft_data, dict):
        await update.message.reply_text(
            "Your saved draft is in the old format. Please run this again:\n"
            f"/draft {opportunity_number}"
        )
        return

    application_id = generate_application_id()

    subject = draft_data.get("subject", f"Application for {opportunity.get('title', 'Opportunity')}")
    body = draft_data.get("email_body", "")
    cover_letter = draft_data.get("cover_letter", "")
    if not body or not cover_letter:
        await update.message.reply_text(
            "Email body or cover letter is missing. Please regenerate the draft:\n"
            f"/draft {opportunity_number}"
        )
        return

    await update.message.reply_text(
        "Creating CV PDF and Cover Letter PDF. Please wait..."
    )

    try:
        cv_pdf = save_cv_as_pdf(
            cv_text=final_cv,
            opportunity=opportunity,
            opportunity_number=opportunity_number
        )

        cover_letter_pdf = save_cover_letter_as_pdf(
            cover_letter_text=cover_letter,
            opportunity=opportunity,
            opportunity_number=opportunity_number
        )

        final_body = (
            body
            + "\n\nAttachments:\n"
            + "1. CV\n"
            + "2. Cover Letter\n\n"
            + f"Reference ID: {application_id}"
        )
        await update.message.reply_text(
            f"Sending email to {recipient_email}...\n\nSubject:\n{subject}"
        )

        send_result = send_email_with_attachments(
        recipient_email=recipient_email,
        subject=subject,
        body=final_body,
        attachment_paths=[cv_pdf, cover_letter_pdf]
        )

        log_agent_action(
        agent="Email Sender Agent",
        action="email_sent",
        outcome="OK",
        notes=f"Email sent for opportunity {opportunity_number} to {recipient_email}"
        )
        session_id = cv_data.get("session_id", "")

        log_email_sent(
            application_id=application_id,
            session_id=session_id,
            opportunity_number=opportunity_number,
            opportunity=opportunity,
            recipient_email=recipient_email,
            subject=subject,
            cv_file=cv_pdf,
            notes=f"Sent from ApplyPilot Telegram bot. Cover letter: {cover_letter_pdf}"
        )

        if "sent_applications" not in context.user_data:
            context.user_data["sent_applications"] = {}

        context.user_data["sent_applications"][application_id] = {
            "opportunity_number": opportunity_number,
            "recipient_email": recipient_email,
            "subject": subject,
            "cv_pdf": cv_pdf,
            "cover_letter_pdf": cover_letter_pdf,
            "send_result": send_result
        }

        await update.message.reply_text(
            f"Email sent successfully.\n\n"
            f"Application ID:\n{application_id}\n\n"
            f"Sent attachments:\n"
            f"- CV PDF\n"
            f"- Cover Letter PDF\n\n"
            f"CSV updated:\ndata/application_tracker.csv\n\n"
            f"Later, use /checkreplies to check for a response."
        )

    except Exception as error:
        await update.message.reply_text(
            f"Email sending failed.\n\nError:\n{error}"
        )

async def checkreplies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Checking inbox for replies. Please wait...")

    try:
        result = await asyncio.to_thread(check_replies_and_update_tracker)

        log_agent_action(
            agent="Reply Tracking Agent",
            action="manual_reply_check",
            outcome="OK",
            notes=f"Checked={result.get('checked', 0)}; replies_found={result.get('replies_found', 0)}"
        )

        summary = (
            f"{result.get('message', 'Reply check completed.')}\n\n"
            f"Pending applications checked: {result.get('checked', 0)}\n"
            f"Replies found: {result.get('replies_found', 0)}\n\n"
            f"CSV updated:\ndata/application_tracker.csv"
        )

        await update.message.reply_text(summary)

    except Exception as error:
        log_agent_action(
            agent="Reply Tracking Agent",
            action="manual_reply_check",
            outcome="FAILED",
            notes=str(error)
        )

        await update.message.reply_text(
            f"Reply check failed.\n\nError:\n{error}"
        )
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = format_status_rows(limit=10)

    for part in split_message(status_text):
        await update.message.reply_text(part)


NOTIFY_CHAT_FILE = "data/notify_chat_id.txt"


def save_notify_chat_id(chat_id: int):
    os.makedirs("data", exist_ok=True)

    with open(NOTIFY_CHAT_FILE, "w", encoding="utf-8") as file:
        file.write(str(chat_id))


def load_notify_chat_id():
    if not os.path.exists(NOTIFY_CHAT_FILE):
        return None

    with open(NOTIFY_CHAT_FILE, "r", encoding="utf-8") as file:
        value = file.read().strip()

    if not value:
        return None

    return int(value)


async def notifyon_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    save_notify_chat_id(chat_id)

    await update.message.reply_text(
        "Automatic reply notifications are now ON.\n\n"
        "ApplyPilot will check email replies in the background and notify this Telegram chat."
    )


async def notifyoff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists(NOTIFY_CHAT_FILE):
        os.remove(NOTIFY_CHAT_FILE)

    await update.message.reply_text(
        "Automatic reply notifications are now OFF."
    )


async def auto_check_replies_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = load_notify_chat_id()

    if not chat_id:
        return

    try:
      result = await asyncio.to_thread(check_replies_and_update_tracker)
      log_agent_action(
      agent="Reply Tracking Agent",
      action="manual_reply_check",
      outcome="OK",
      notes=f"Checked={result['checked']}; replies_found={result['replies_found']}"
      )
    except Exception as error:
        print(f"Auto reply check failed: {error}")
        return

    new_replies = result.get("new_replies", [])

    for reply in new_replies:
        message = f"""
New Application Reply Received

Application ID:
{reply.get("application_id")}

Opportunity:
{reply.get("opportunity_title")}

Organization:
{reply.get("organization")}

Reply From:
{reply.get("reply_from")}

Subject:
{reply.get("reply_subject")}

Received At:
{reply.get("reply_received_at")}

Email Preview:
{reply.get("reply_body_preview", "No readable email body found.")}

CSV updated:
data/application_tracker.csv
"""
        await context.bot.send_message(
            chat_id=chat_id,
            text=message.strip()
        )

async def evaluate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refined_versions = context.user_data.get("refined_cv_versions", {})
    application_drafts = context.user_data.get("application_drafts", {})

    if not context.args:
        await update.message.reply_text(
            "Please choose an opportunity number.\n\nExample:\n/evaluate 1"
        )
        return

    opportunity_number = context.args[0]

    if opportunity_number not in refined_versions:
        await update.message.reply_text(
            "No CV found for this opportunity. Use /campaign or /refinecv first."
        )
        return

    if opportunity_number not in application_drafts:
        await update.message.reply_text(
            f"No draft found for this opportunity. Use:\n/draft {opportunity_number}"
        )
        return

    cv_data = refined_versions[opportunity_number]

    if cv_data.get("status") != "finalized":
        await update.message.reply_text(
            f"CV is not finalized yet. Use:\n/finalizecv {opportunity_number}"
        )
        return

    draft_data = application_drafts[opportunity_number]["draft"]

    if not isinstance(draft_data, dict):
        await update.message.reply_text(
            f"Draft is in old format. Regenerate it:\n/draft {opportunity_number}"
        )
        return

    evaluation = evaluate_application_package(
        opportunity_number=opportunity_number,
        opportunity=cv_data["opportunity"],
        final_cv=cv_data["refined_cv"],
        draft_data=draft_data
    )
    log_agent_action(
    agent="Evaluation Agent",
    action="application_package_evaluated",
    outcome=evaluation.get("final_status", "unknown").upper(),
    notes=f"Opportunity {opportunity_number}; score={evaluation.get('score')}/100"
    )

    if "evaluation_results" not in context.user_data:
        context.user_data["evaluation_results"] = {}

    context.user_data["evaluation_results"][opportunity_number] = evaluation

    report = format_evaluation_report(evaluation)

    for part in split_message(report):
        await update.message.reply_text(part)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """
ApplyPilot Commands

Main Workflow:
/start - Start ApplyPilot and enable reply notifications
/help - Show all commands
/campaign - Start full application workflow
/cancel - Cancel current workflow

Opportunity Search:
/search - Search opportunities only
/select 1 2 3 - Shortlist opportunities

CV Workflow:
/refinecv 1 - Refine CV for selected opportunity
/revisecv 1 - Revise CV using your feedback
/finalizecv 1 - Finalize CV for an opportunity
/showcampaigncv 1 - Show campaign-generated CV
/downloadcv 1 - Download finalized CV if available

Application Drafting:
/draft 1 - Generate cover letter and email draft
/evaluate 1 - Check CV, cover letter, and email before sending
/sendemail 1 email@example.com - Send email with CV PDF and cover letter PDF

Reply Tracking:
/checkreplies - Manually check inbox for replies
/status - Show application tracker status
/notifyon - Turn on automatic reply notifications
/notifyoff - Turn off automatic reply notifications

Example Full Flow:
/campaign
Upload CV
Computer vision PhD Germany
/showcampaigncv 1
/finalizecv 1
/draft 1
/evaluate 1
/sendemail 1 test@email.com
/checkreplies
/status
"""
    await update.message.reply_text(message.strip())

async def telegram_activity_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat

        user_id = user.id if user else ""
        username = user.username if user else ""
        chat_id = chat.id if chat else ""

        message_type = "unknown"
        command = ""
        text = ""
        file_name = ""

        if update.message:
            if update.message.text:
                text = update.message.text.strip()
                message_type = "text"

                if text.startswith("/"):
                    command = text.split()[0]

            elif update.message.document:
                message_type = "document"
                file_name = update.message.document.file_name or ""

            elif update.message.photo:
                message_type = "photo"

            elif update.message.voice:
                message_type = "voice"

            else:
                message_type = "other_message"

        elif update.callback_query:
            message_type = "callback_query"
            text = update.callback_query.data or ""

        log_telegram_event(
            user_id=user_id,
            username=username,
            chat_id=chat_id,
            message_type=message_type,
            command=command,
            text=text,
            file_name=file_name
        )

    except Exception as error:
        print(f"Telegram activity logging failed: {error}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing in .env file")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("apply", apply)],
        states={
            WAITING_GOAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_goal)
            ],
            WAITING_CV: [
                MessageHandler(filters.Document.ALL, receive_cv_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_cv_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    campaign_handler = ConversationHandler(
        entry_points=[CommandHandler("campaign", campaign_command)],
        states={
            WAITING_CAMPAIGN_CV: [
                MessageHandler(filters.Document.ALL, receive_campaign_cv_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_campaign_cv_text),
            ],
            WAITING_CAMPAIGN_GOAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_campaign_goal),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    search_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_command)],
        states={
            WAITING_SEARCH_KEYWORDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_keywords)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


    refinecv_handler = ConversationHandler(
        entry_points=[CommandHandler("refinecv", refinecv_command)],
        states={
            WAITING_REFINE_CV: [
                MessageHandler(filters.Document.ALL, receive_refine_cv_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_refine_cv_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    revisecv_handler = ConversationHandler(
        entry_points=[CommandHandler("revisecv", revisecv_command)],
        states={
            WAITING_REVISE_CV: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_revise_cv_feedback)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL, telegram_activity_logger), group=-1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conversation_handler)
    app.add_handler(search_handler)
    app.add_handler(CommandHandler("select", select_command))
    app.add_handler(refinecv_handler)
    app.add_handler(revisecv_handler)
    app.add_handler(CommandHandler("finalizecv", finalizecv_command))
    app.add_handler(CommandHandler("draft", draft_command))
    app.add_handler(campaign_handler)
    app.add_handler(CommandHandler("sendemail", sendemail_command))
    app.add_handler(CommandHandler("checkreplies", checkreplies_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("showcampaigncv", showcampaigncv_command))
    app.add_handler(CommandHandler("evaluate", evaluate_command))
    app.add_handler(CommandHandler("notifyon", notifyon_command))
    app.add_handler(CommandHandler("notifyoff", notifyoff_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, normal_chat))
    
    # Normal chat handler. This works outside /apply flow.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, normal_chat))
    if app.job_queue:
        app.job_queue.run_repeating(
            auto_check_replies_job,
            interval=500,
            first=60,
            job_kwargs={
                "max_instances": 1,
                "coalesce": True,
                "misfire_grace_time": 120
            }
        )
    else:
        print("JobQueue is not available. Install: pip install 'python-telegram-bot[job-queue]'")
    print("ApplyPilot Telegram Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
