# ApplyPilot

**A private agentic assistant for application search, CV tailoring, evaluation, email sending, reply tracking, usage logging, and MCP-based inspection.**

---

## Team

**Team Name:** ApplyPilot Team

**Members:**
- Muhammad Usman
- Mohammad Umar

**Affiliation:** Department of Electrical Engineering and Computer Science, Gwangju Institute of Science and Technology, Korea

---

## Primary Project Type

ApplyPilot is a **practical private agentic AI assistant**. It is designed as an application workflow assistant that helps users search academic or professional opportunities, tailor CVs, draft application materials, evaluate the final package, send approved emails, and track replies.

The system is implemented as a **Telegram Bot-based workflow** with specialist agents, tool integrations, local model support, evidence logs, and an OpenClaw/MCP inspection layer.

---

## Problem Statement and Target User

Applying to academic and professional opportunities is repetitive, time-consuming, and difficult to manage. Students and early-career researchers often need to:

- Search across noisy job boards, university pages, lab pages, professor pages, and scholarship websites
- Identify relevant MS, PhD, internship, research assistant, or job opportunities
- Tailor the CV for each opportunity
- Draft cover letters and application emails
- Check whether the application package is complete before sending
- Send emails with the correct attachments
- Track which applications were sent and whether replies were received

Manual tracking can easily become disorganized, especially when a user applies to many opportunities.

**Target users:**
- Graduate students looking for MS or PhD positions
- Researchers applying for academic or research assistant roles
- Early-career professionals applying to jobs or internships
- Users who want a private, auditable application workflow rather than a generic chatbot response

ApplyPilot addresses this by creating a structured workflow from CV upload to reply tracking.

---

## Repository Structure

This repository follows the required course structure:

```text
/code
/slides
/paper
/usage-log
/demo-video
README.md
```

Suggested mapping for this project:

```text
/code
  ApplyPilot source code, agents, tools, prompts, configuration examples, and MCP server

/slides
  Final presentation slides

/paper
  IEEE-style term paper/report

/usage-log
  7-day usage log and evidence records

/demo-video
  Demo video or link to the recorded demo

README.md
  Main project documentation and evidence index
```

The implementation also uses these internal folders:

```text
agents/
  Specialist agents such as CV refiner, draft agent, campaign agent, evaluation agent, intake agent, and chat agent

tools/
  Search, email, CV reader, document exporter, tracker, logger, Ollama client, and intent detector tools

data/
  Local application tracker, generated CVs, cover letters, uploads, logs, and session artifacts

docs/
  Architecture, data flow, approval policy, cost report, threat model, and workflow documentation

agent_cards/
  Human-readable descriptions of each agent

skills/
  Workflow-specific skill descriptions

mcp_server/
  Custom ApplyPilot MCP inspection server

usage_log/
  Human-readable usage log evidence
```

---

## Telegram Bot Integration

ApplyPilot is integrated with a **Telegram Bot**, which is the main user-facing interface of the system.

The Telegram Bot allows the user to run the complete application workflow from a chat interface. The bot receives user commands, uploaded CV files, search goals, revision feedback, email-sending instructions, and reply-checking requests.

The Telegram integration is implemented mainly in:

```text
code/bot.py
```

The Telegram Bot is responsible for:

- Receiving commands such as `/start`, `/campaign`, `/draft`, `/evaluate`, and `/sendemail`
- Accepting uploaded CV files
- Asking the user for campaign/search goals
- Routing tasks to workflow functions and specialist agents
- Showing opportunities, tailored CVs, drafts, and evaluation results
- Triggering approved email sending
- Triggering manual or automatic reply checks
- Saving notification chat IDs for reply notifications
- Logging Telegram activity for audit evidence

Telegram is the **main action workflow layer**. The OpenClaw/MCP layer is used for safe inspection and diagnostics, while important actions such as CV finalization, email sending, and reply checking remain controlled through Telegram commands.

Example Telegram workflow:

```text
/start
/help
/campaign
Upload CV
Computer vision PhD Germany
/showcampaigncv 1
/revisecv 1
/finalizecv 1
/draft 1
/evaluate 1
/sendemail 1 test_recipient@example.com
/checkreplies
/status
```

This Telegram integration makes ApplyPilot practical because the user can run the full workflow from a familiar messaging app without needing a separate frontend.

---

## System Overview

ApplyPilot supports both normal chat and structured application commands.

Main workflow:

```text
/start
/campaign
Upload CV
Enter search goal
/showcampaigncv 1
/revisecv 1
/finalizecv 1
/draft 1
/evaluate 1
/sendemail 1 recipient@example.com
/checkreplies
/status
```

The system supports:

- Telegram-based user interaction
- General chat
- Campaign workflow
- CV upload and parsing
- Academic intent detection
- Opportunity search and ranking
- CV tailoring
- CV revision based on user feedback
- CV finalization
- Cover letter and email draft generation
- Evaluation Agent before sending
- Email sending with CV PDF and cover letter PDF
- Reply tracking through Gmail IMAP
- Application tracker CSV
- Usage and activity logs
- OpenClaw/MCP-based inspection layer

---

## Architecture

ApplyPilot is organized into six layers:

1. **Telegram Interface Layer**  
   Handles Telegram commands, messages, CV uploads, workflow interaction, and user notifications.

2. **Core Workflow Layer**  
   Coordinates campaign execution, search, ranking, CV tailoring, drafting, evaluation, sending, and reply tracking.

3. **Specialist Agent Layer**  
   Includes focused agents for search, ranking, CV refinement, drafting, evaluation, intake, and general chat.

4. **Tool and Integration Layer**  
   Connects to Tavily search, Ollama, Gmail SMTP/IMAP, document export tools, and CSV trackers.

5. **Storage and Evidence Layer**  
   Stores generated CVs, cover letters, uploaded files, application tracker CSV, logs, usage records, and evidence files.

6. **OpenClaw + MCP Inspection Layer**  
   Provides a diagnostic inspection gateway through a custom FastMCP server. Telegram remains the main action workflow, while MCP exposes safe project artifacts such as status, latest logs, and tracker summaries.

---

## Main Agents

| Agent | Role |
|---|---|
| Campaign Agent | Coordinates the full application campaign workflow |
| Search/Ranking Agent | Searches opportunities and ranks them against the user goal |
| CV Refiner Agent | Tailors the CV for selected opportunities |
| Draft Agent | Generates cover letters and email drafts |
| Evaluation Agent | Checks the final CV, cover letter, email body, and subject before sending |
| Email/Reply Tracking Agent | Sends approved emails and checks replies |
| Chat Agent | Handles general conversation outside the application workflow |

The Telegram bot, mainly implemented in `bot.py`, acts as the primary orchestrator.

---

## Tools, Models, and Data Paths

| Component | Use |
|---|---|
| Telegram Bot | Main user interface and action workflow |
| Tavily API | Real-time opportunity search |
| Academic Intent Detector | Detects MS, PhD, scholarship, professor, lab, and academic queries |
| Ollama | Local model for CV refinement and draft generation |
| Gemini/Groq | Optional backup cloud model support |
| CV Reader | Reads uploaded PDF, DOCX, or TXT CV files |
| Document Exporter | Generates DOCX/PDF CVs and cover letters |
| Gmail SMTP | Sends approved application emails |
| Gmail IMAP | Checks inbox replies |
| CSV Tracker | Stores application status, reply status, and notification status |
| Usage Log | Records workflow evidence |
| OpenClaw/MCP | Provides inspection and diagnostic access |

Evidence files include:

```text
code/data/application_tracker.csv
usage-log/USAGE_LOG.md
code/data/final_cvs/
code/data/cover_letters/
code/data/logs/
```

---

## Installation Instructions

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-repository-name>/code
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and run Ollama

Install Ollama from:

```text
https://ollama.com
```

Pull a local model:

```bash
ollama pull llama3.1:8b
```

Start Ollama:

```bash
ollama serve
```

### 5. Create `.env`

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Fill in the required values:

```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TAVILY_API_KEY=your_tavily_api_key

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b

EMAIL_USER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993

GEMINI_API_KEY=optional_backup_key
```

Do not commit `.env` to GitHub.

---

## Telegram Bot Setup

### 1. Create a Telegram bot

1. Open Telegram.
2. Search for `@BotFather`.
3. Send:

```text
/newbot
```

4. Follow the instructions and copy the bot token.
5. Add the token to `.env`:

```text
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 2. Run the bot

```bash
python bot.py
```

Expected terminal output:

```text
ApplyPilot Telegram Bot is running...
```

### 3. Open the bot in Telegram

Start the bot:

```text
/start
```

Show all commands:

```text
/help
```

Start the full workflow:

```text
/campaign
```

---

## Execution Instructions

Run the Telegram bot:

```bash
python bot.py
```

Open Telegram and use:

```text
/start
/help
/campaign
```

Example full workflow:

```text
/campaign
Upload CV
Computer vision PhD Germany
/showcampaigncv 1
/revisecv 1
/finalizecv 1
/draft 1
/evaluate 1
/sendemail 1 test_recipient@example.com
/checkreplies
/status
```

---

## Main Commands

| Command | Purpose |
|---|---|
| `/start` | Start ApplyPilot |
| `/help` | Show available commands |
| `/campaign` | Start full application workflow |
| `/search` | Search opportunities only |
| `/select` | Shortlist opportunities |
| `/showcampaigncv 1` | Show generated campaign CV |
| `/refinecv 1` | Refine CV for an opportunity |
| `/revisecv 1` | Revise CV using user feedback |
| `/finalizecv 1` | Finalize CV |
| `/draft 1` | Generate cover letter and email |
| `/evaluate 1` | Run Evaluation Agent |
| `/sendemail 1 email@example.com` | Send approved application email |
| `/checkreplies` | Check inbox replies |
| `/status` | Show application tracker status |
| `/notifyon` | Enable reply notifications |
| `/notifyoff` | Disable reply notifications |
| `/cancel` | Cancel current workflow |

---

## Differentiation vs Big-Tech Assistants and Platforms

ApplyPilot is different from general-purpose big-tech assistants because it is designed for one practical workflow rather than open-ended conversation.

Key differences:

1. **Workflow-specific design**  
   ApplyPilot is not only a chat assistant. It has a complete application pipeline from search to reply tracking.

2. **Telegram-based practical interface**  
   The system is integrated into Telegram, allowing the user to run the workflow from a familiar messaging app.

3. **Human approval gate**  
   It does not send emails automatically. The user must explicitly approve sending with `/sendemail`.

4. **Private local model option**  
   CV refinement and draft generation can be handled through Ollama locally, reducing the need to send private CV data to cloud models.

5. **Auditable evidence**  
   Application actions are recorded in CSV trackers and usage logs, making the workflow inspectable.

6. **Email reply tracking**  
   ApplyPilot checks Gmail replies and updates application status, which general chatbots do not normally provide as an integrated workflow.

7. **Academic intent detection**  
   The system detects academic queries such as MS, PhD, scholarship, professor, lab, and doctoral searches.

8. **MCP inspection layer**  
   OpenClaw/MCP provides a safe inspection and diagnostic layer over project artifacts while Telegram remains the main action interface.

---

## 7-Day Usage Log Summary

The usage log shows that ApplyPilot was tested beyond the minimum required 7-day window. The main 7-day evidence period runs from **Day 1 to Day 7**, with additional monitoring records continuing into Day 8 and Day 9. During this period, the system was tested through the full application workflow: campaign start, CV upload, opportunity search, CV tailoring, revision, finalization, draft generation, evaluation, email sending, reply checking, and status/log monitoring.

### Overall 7-Day Summary

| Metric | Count / Evidence |
|---|---:|
| Logged evidence period used for summary | Day 1 to Day 7 |
| Total log rows in Day 1–Day 7 window | 1,133 |
| Telegram command entries in Day 1–Day 7 window | 215 |
| Completed campaign workflows | 18 |
| Drafts generated | 27 |
| Evaluation Agent runs | 22 |
| Emails sent through ApplyPilot | 10 |
| Reply-check actions | 813 |
| Reply detections recorded in logs | 12 |
| Standalone search workflows completed | 1 |

### Day-by-Day Usage Summary

| Day | Date / Period | Main Activities | Evidence Summary |
|---|---|---|---|
| Day 1 | 2026-06-06 | Initial command and logging validation | `/start`, `/help`, `/campaign`, `/checkreplies`, `/cancel`, day separator test, and reply-check logging were tested. |
| Day 2 | 2026-06-07 | First structured campaign test | Campaign goal was received for **Computer Vision PhD Germany**. Campaign search, ranking, CV drafts, revision, finalization, draft generation, and Evaluation Agent testing were performed. |
| Day 3 | 2026-06-08 | Main end-to-end system testing | This was the strongest test day. Multiple campaigns were completed, drafts were generated, evaluations were run, emails were sent, and replies were detected. The workflow included `/campaign`, `/showcampaigncv`, `/revisecv`, `/finalizecv`, `/draft`, `/evaluate`, `/sendemail`, `/checkreplies`, and `/status`. |
| Day 4 | 2026-06-10 | South Korea academic workflow test | A campaign for **Computer Vision PhD in South Korea** was completed. The system generated a draft for opportunity 3, evaluated it with **100/100**, sent an email, checked replies multiple times, and later detected one reply. |
| Day 5 | 2026-06-11 | Continuous monitoring | The bot continued scheduled/manual reply tracking. The log confirms persistent background reply-check behavior even when no new replies were found. |
| Day 6 | 2026-06-12 | Monitoring and status validation | Reply tracking continued throughout the day, and user commands such as `/start`, `/apply`, `/cancel`, and `/status` were recorded. |
| Day 7 | 2026-06-13 | Long-running reply-tracking evidence | The system continued automated/manual reply-check activity throughout the day, showing stability of the monitoring loop. |

### Key Workflow Evidence

The usage log confirms that ApplyPilot successfully executed the core workflow:

```text
/campaign
→ campaign_goal_received
→ campaign_completed
→ /showcampaigncv
→ /revisecv
→ /finalizecv
→ /draft
→ draft_generated
→ /evaluate
→ application_package_evaluated
→ /sendemail
→ email_sent
→ /checkreplies
→ manual_reply_check
→ /status
```

### Important Observations

- The log confirms that ApplyPilot is not only a demo chatbot; it maintains an auditable workflow history.
- The campaign workflow was repeatedly tested with academic PhD queries such as **Computer Vision PhD Germany**, **Computer Vision PhD Australia**, and **Computer Vision PhD in South Korea**.
- The Evaluation Agent was tested with different outcomes, including `FAILED`, `FAIL`, `PASS`, `NEEDS_REVIEW`, and `APPROVED`. This shows that the system does not blindly approve every generated application package.
- Email sending was tested through the Email Sender Agent, and reply tracking was verified through repeated `manual_reply_check` entries.
- The reply tracker continued running across multiple days, which supports the claim that ApplyPilot can monitor application replies after an email has been sent.
- Additional Day 8 and Day 9 records exist beyond the required 7-day period, showing extended monitoring and continued system operation.

### README Summary Statement

ApplyPilot was tested over a 7-day usage window with more than **1,100 logged records**, including **18 completed campaign workflows**, **27 generated drafts**, **22 evaluation runs**, **10 sent emails**, and **813 reply-check actions**. The logs show successful end-to-end application workflows as well as long-running reply-monitoring behavior. This provides evidence for practicality, auditability, and workflow stability.

---

## Cost Estimate and Local/Cloud Stack Discussion

ApplyPilot was designed to minimize cost while keeping the system practical.

### Local stack

| Component | Cost | Purpose |
|---|---|---|
| Python bot | Free | Core workflow |
| Ollama | Free | Local CV and draft generation |
| Local CSV/log files | Free | Evidence tracking |
| OpenClaw/MCP local inspection | Free | Diagnostic inspection layer |

### Cloud/API stack

| Component | Cost Type | Purpose |
|---|---|---|
| Telegram Bot API | Free | User interface |
| Tavily API | Free/limited tier | Live opportunity search |
| Gmail SMTP/IMAP | Free with Gmail account | Sending and reply tracking |
| Gemini/Groq backup | Free/limited or paid | Optional backup generation |

The current implementation uses free or low-cost APIs where possible. Some limitations are due to free or lightweight APIs. Search relevance, country filtering, and document quality can be improved significantly by replacing the current free search/model APIs with stronger paid APIs. The system architecture is modular, so the workflow can remain the same while the underlying search or model provider is upgraded.

Estimated current cost for testing:

```text
Approximate cost: $0 to low-cost API usage, depending on search/model provider limits.
```

Future paid-stack improvement:

```text
Better paid search API + stronger paid language model
→ higher opportunity relevance
→ better factual consistency
→ stronger CV/cover letter quality
→ less noisy academic search results
```

---

## Privacy and Security Summary

ApplyPilot handles sensitive user data such as CV content, email addresses, application history, generated documents, and reply previews. The system includes the following privacy and security decisions:

1. **Local-first processing**
   - CV refinement and drafting can run through Ollama locally.
   - Sensitive CV text does not need to be sent to a cloud LLM by default.

2. **Secrets stored outside code**
   - API keys, Telegram bot token, and Gmail app password are stored in `.env`.
   - `.env` must not be committed to GitHub.

3. **Human approval before sending**
   - Email sending requires `/sendemail`.
   - The system does not automatically send applications.

4. **Evaluation before sending**
   - The Evaluation Agent checks the CV, cover letter, email body, and subject.
   - It can return pass, warning, or fail status.

5. **Controlled MCP layer**
   - MCP is used for safe inspection and diagnostics.
   - It does not replace the Telegram action workflow.

6. **Evidence with caution**
   - Logs and CSV trackers are useful for inspection.
   - Public repository versions should remove or anonymize private emails, CV files, generated PDFs, and personal tracker data.

Recommended `.gitignore` entries:

```text
.env
venv/
__pycache__/
data/uploads/
data/final_cvs/
data/cover_letters/
data/logs/
data/application_tracker.csv
data/notify_chat_id.txt
```

---

## Demo Video

Demo video link:

```text
<add YouTube/Google Drive/GitHub release demo video link here>
```

The demo should be 5 minutes or less and show:

1. Starting ApplyPilot
2. Running `/campaign`
3. Uploading CV
4. Entering an academic search goal
5. Viewing generated opportunities
6. Showing CV draft
7. Finalizing CV
8. Drafting cover letter/email
9. Running `/evaluate`
10. Sending test email
11. Checking replies and status

---

## Paper and Slides

Final paper/report:

```text
/paper/ApplyPilot_IEEE_Term_Report_Final_With_Tracker_Logs.docx
/paper/ApplyPilot_IEEE_Term_Report_Final_With_Tracker_Logs.pdf
```

Final slides:

```text
/slides/GEN_AI.pdf
/slides/GEN_AI.pptx
```

---

## Evidence Links

Important evidence files:

```text
/usage-log/USAGE_LOG.md
/code/data/application_tracker.csv
/code/data/logs/agent_actions.jsonl
/code/data/logs/telegram_activity.jsonl
```

Before public submission, private emails, CVs, generated PDFs, and credentials should be removed or anonymized.

---

## Grading Alignment

| Rubric Category | How ApplyPilot Addresses It |
|---|---|
| Practicality | Solves real application workflow from search to reply tracking |
| Cost Economy | Uses local Ollama and free/low-cost APIs where possible |
| Privacy and Security | Local processing, `.env` secrets, approval gate, safe MCP inspection |
| Differentiation vs Big Tech | Workflow-specific, Telegram-integrated, auditable, private, and integrated with email/tracker |
| Technical Rigour | Multi-agent architecture, tools, logs, tracker, evaluation, MCP layer |
| Smartening | Academic intent detection, ranking, CV tailoring, Evaluation Agent |
| Documentation and Demo | README, paper, slides, usage log, tracker evidence, demo video |

---

## Current Status

ApplyPilot currently supports:

- Telegram Bot integration
- Telegram command-based workflow
- General chat
- CV upload
- Academic search detection
- Opportunity search and ranking
- CV tailoring and revision
- Cover letter and email drafting
- Evaluation Agent
- Approved email sending
- Reply tracking
- Application tracker CSV
- Usage log and activity logs
- OpenClaw/MCP inspection layer

The system has been tested through end-to-end workflows and documented through screenshots, CSV tracker evidence, and usage logs.

