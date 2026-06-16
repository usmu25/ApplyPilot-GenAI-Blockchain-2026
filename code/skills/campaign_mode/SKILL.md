# Skill: Campaign Mode

## Purpose
Run the complete ApplyPilot workflow with minimum user involvement.

## Inputs
- User CV file or CV text
- Search goal or keywords

## Steps
1. Receive CV.
2. Extract CV text.
3. Ask user for search goal.
4. Run Intake Agent.
5. Search real-time opportunities.
6. Parse opportunities.
7. Rank top opportunities.
8. Generate tailored CV drafts for top results.
9. Show summary to user.
10. Wait for user review, revision, or finalization.

## Tools Used
- CV Reader
- Tavily Search
- Opportunity Parser
- Ranking Agent
- Ollama
- Agent Logger

## Approval Needed
No approval needed for search, ranking, or drafting.
Approval is required before sending any email.

## Output
- Top opportunities
- Tailored CV drafts
- Logs
- Stored session data
