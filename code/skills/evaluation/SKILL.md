# Skill: Application Package Evaluation

## Purpose
Check whether a CV, cover letter, and email draft are ready before sending.

## Inputs
- Finalized CV
- Draft cover letter
- Draft email body
- Opportunity details

## Checks
1. CV is not too short.
2. CV does not contain assistant explanation text.
3. Cover letter is present.
4. Email body is present.
5. Email subject is clean.
6. Email mentions attachments.
7. No obvious spammy phrases.
8. Opportunity title and organization are available.

## Output
- PASS
- WARNING
- FAIL
- Score out of 100
- List of issues

## Human Review
If status is WARNING, user should review before sending.
If status is FAIL, user should fix the package before sending.
