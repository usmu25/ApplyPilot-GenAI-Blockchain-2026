# ApplyPilot Data Flow

## Local Data
- Uploaded CV files
- Extracted CV text
- Refined CV drafts
- Final CV PDFs
- Cover letter PDFs
- Agent logs
- Application tracker CSV

## External Data
- Tavily search results
- Gmail SMTP sent emails
- Gmail IMAP inbox replies

## Routing Decisions
- CV text is processed locally using Ollama.
- General chat is handled locally using Ollama.
- Opportunity search queries go to Tavily.
- Email sending goes through Gmail SMTP only after user approval.
- Reply tracking reads Gmail inbox through IMAP.

## Sensitive Data
Sensitive data includes:
- CV content
- Email addresses
- Gmail app password
- API keys
- Application history

## Protection Rules
- Store secrets in .env.
- Do not commit .env to GitHub.
- Do not send emails without /sendemail.
- Do not send raw CV data to cloud LLMs by default.
- Treat search results and email replies as untrusted text.
