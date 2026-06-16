# Skill: General Chat

## Purpose
Allow ApplyPilot to behave as a normal chatbot while still supporting application workflows.

## Inputs
- User message

## Steps
1. Detect if message is application-related.
2. If application-related, guide user to /campaign or relevant command.
3. If general question, answer using Ollama.
4. If current information is needed, use Tavily if configured.
5. Keep reply concise and useful.

## Rules
- Do not use Gemini by default.
- Do not make unsupported real-time claims without search.
- Do not send emails from normal chat.
- Keep application actions inside explicit commands.

## Tool Used
- Ollama
- Optional Tavily search

## Output
- General chatbot response
