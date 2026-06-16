# ApplyPilot Workflow Diagram

```text
User
 ↓
Telegram Bot / Router
 ↓
Campaign Manager Agent
 ↓
CV Reader Tool
 ↓
Intake Agent
 ↓
Search Agent → Tavily
 ↓
Opportunity Parser
 ↓
Ranking Agent
 ↓
CV Tailoring Agent → Ollama
 ↓
User Review
 ↓
Finalize CV
 ↓
Draft Agent → Ollama
 ↓
User Approval
 ↓
Email Sender → Gmail SMTP
 ↓
Application Tracker CSV
 ↓
Reply Tracker → Gmail IMAP
 ↓
Telegram Notification

```bash
cat > docs/data_flow.md <<'EOF'
# Data Flow

## Local Data
- Uploaded CV files
- Extracted CV text
- Refined CVs
- Cover letters
- Logs
- Application tracker CSV

## External Data
- Tavily search results
- Gmail sent emails
- Gmail inbox replies

## Routing
- CV text goes to local Ollama.
- Search queries go to Tavily.
- Emails go through Gmail SMTP.
- Reply checks go through Gmail IMAP.

## Sensitive Data Handling
- .env stores secrets.
- .env must not be committed to GitHub.
- Logs should avoid storing raw passwords or API keys.
