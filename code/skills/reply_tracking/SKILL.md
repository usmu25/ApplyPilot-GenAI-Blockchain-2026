# Skill: Reply Tracking

## Purpose
Track replies to sent application emails and notify the user.

## Inputs
- application_tracker.csv
- Gmail inbox
- sent email subject
- recipient email

## Steps
1. Read pending applications from CSV.
2. Check Gmail inbox using IMAP.
3. Match replies by subject, sender, or application reference.
4. Update CSV reply status.
5. Send Telegram notification if a reply is found.
6. Display email preview when available.

## Tools Used
- Gmail IMAP
- Application Tracker
- Telegram Bot

## Approval Needed
No approval needed for reading replies after user enables notifications.

## Output
- Updated CSV
- Telegram notification
- Reply preview
