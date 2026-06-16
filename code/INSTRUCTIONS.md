# ApplyPilot Global Instructions

## Core Workflow
User uploads a CV, searches opportunities, reviews tailored CVs, finalizes a CV, generates a cover letter/email draft, evaluates the package, sends email after approval, and tracks replies.

## Model Routing
- Use Ollama for private CV processing, drafting, and general chat.
- Use Tavily for real-time search.
- Gmail SMTP/IMAP is used for sending and reply tracking.
- Gemini/Groq may exist as backup but should not be default for private CV processing.

## Approval Policy
The system may search, draft, evaluate, and check replies automatically.
The system must not send email unless the user explicitly runs /sendemail.

## Logging
Log major agent actions, errors, email status, reply status, and evaluation output.
