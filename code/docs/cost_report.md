# Cost Report

## Model Strategy
ApplyPilot uses a two-tier cost strategy.

## Local Model
- Ollama is used for general chat, CV refinement, CV revision, cover letter generation, and email draft generation.
- This reduces token/API cost and keeps private CV data local.

## External APIs
- Tavily is used for real-time opportunity search.
- Gmail SMTP/IMAP is used for sending and tracking application emails.

## Cost Control
- Gemini/Groq/OpenAI are not used by default.
- Email sending requires human approval.
- Background reply checking runs at fixed intervals to avoid unnecessary API calls.

## Estimated Monthly Cost
For demo use, the expected cost is low because most LLM work runs locally through Ollama.
