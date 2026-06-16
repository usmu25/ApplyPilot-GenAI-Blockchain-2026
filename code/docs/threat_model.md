# Threat Model

Sensitive data:
- CV content
- Email addresses
- API keys
- Gmail app password
- Application tracker

Main risks:
- Fake CV content
- Email sent without approval
- API key leakage
- Prompt injection from web pages or email replies
- Missed reply notification

Mitigations:
- Use Ollama locally for private text.
- Keep secrets in .env.
- Require /sendemail for email sending.
- Add Evaluation Agent before sending.
- Use CSV tracker and logs.
