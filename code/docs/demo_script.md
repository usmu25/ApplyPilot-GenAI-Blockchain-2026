# ApplyPilot Demo Script

## Demo Goal
Show that ApplyPilot can search opportunities, tailor a CV, generate a cover letter, send an approved email, and track replies.

## Demo Steps

### 1. Start Bot
Run:

python bot.py

In Telegram:

/start

### 2. Start Campaign Mode

/campaign

Upload CV PDF.

Search goal:

Computer vision PhD Germany

### 3. Review Campaign Result

/showcampaigncv 1

### 4. Revise CV

/revisecv 1

Example feedback:

Make the research experience stronger and reduce unrelated technical details.

### 5. Finalize CV

/finalizecv 1

### 6. Generate Cover Letter and Email

/draft 1

### 7. Send Test Email

/sendemail 1 your_other_email@gmail.com

### 8. Check Replies

/checkreplies

### 9. Show Tracker

/status

## Evidence to Show
- Telegram conversation
- CV PDF generated
- Cover letter PDF generated
- application_tracker.csv
- agent_activity.jsonl
- usage_log/USAGE_LOG.md
