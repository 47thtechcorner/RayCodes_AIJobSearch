#!/usr/bin/env python3
"""
Email Response Watcher & Intent Classifier
Monitors candidate email inbox (IMAP) for recruiter/founder replies,
classifies intent (Interview, Technical Screen, Rejection, Auto-ACK),
and automatically updates:
  - outputs/application_board.json
  - outputs/application_board.md
  - outputs/job_applications_tracker.xlsx (Excel)

Designed to run continuously or as part of the 24-hour autopilot loop.
"""

import sys
import os
import re
import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import tracker
import excel_tracker

# Intent Classification Pattern Matchers
INTENT_PATTERNS = {
    "OFFER": [
        r"offer letter",
        r"formal offer",
        r"extending an offer",
        r"delighted to offer",
        r"pleased to offer you",
        r"compensation package",
        r"welcome to the team"
    ],
    "INTERVIEW": [
        r"\binterview\b",
        r"\bspeak with\b",
        r"\bchat with\b",
        r"\bmeet with\b",
        r"\bcalendly\.com\b",
        r"\bzoom\.us\b",
        r"\bmeet\.google\.com\b",
        r"\bnext round\b",
        r"\bnext steps in the process\b",
        r"\bhiring manager wants to connect\b",
        r"\bavailability for a call\b",
        r"\btime to chat\b"
    ],
    "SCREENING": [
        r"\bcoding challenge\b",
        r"\btechnical assessment\b",
        r"\bhackerrank\b",
        r"\bcodesignal\b",
        r"\btake-home\b",
        r"\bonline assessment\b",
        r"\btechnical evaluation\b",
        r"\bcode test\b"
    ],
    "REJECTED": [
        r"\bunfortunately\b",
        r"\bnot moving forward\b",
        r"\bdecided to pursue other candidates\b",
        r"\bposition has been filled\b",
        r"\bnot a match at this time\b",
        r"\bhigh volume of applicants\b",
        r"\bwill not be proceeding\b"
    ],
    "AUTO_ACK": [
        r"\breceived your application\b",
        r"\bthank you for applying\b",
        r"\bapplication submitted\b",
        r"\bcurrently reviewing your application\b",
        r"\bwe have received your resume\b"
    ]
}


def load_env_credentials() -> Dict[str, str]:
    """Reads IMAP credentials from RayCodes or system environment."""
    env_file = BASE_DIR / ".env"
    creds = {
        "IMAP_SERVER": os.getenv("IMAP_SERVER", ""),
        "IMAP_PORT": os.getenv("IMAP_PORT", "993"),
        "IMAP_USER": os.getenv("IMAP_USER", ""),
        "IMAP_PASSWORD": os.getenv("IMAP_PASSWORD", ""),
        "IMAP_SSL": os.getenv("IMAP_SSL", "true")
    }
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in creds and not creds[k]:
                        creds[k] = v
    return creds


def clean_text(text: str) -> str:
    return " ".join(text.split())


def classify_email_intent(subject: str, body: str) -> Tuple[str, str, str, str]:
    """
    Returns (status, response_category, snippet, next_action)
    """
    combined = f"{subject} {body}".lower()

    # 0. Offer Letter
    for pattern in INTENT_PATTERNS.get("OFFER", []):
        if re.search(pattern, combined):
            snippet = extract_snippet(body, pattern)
            return (
                "OFFER",
                "Job Offer Extended",
                clean_text(f"Formal offer extended: '{snippet}'")[:120],
                "🎉 Review offer terms, generate acceptance or negotiation draft"
            )

    # 1. Interview Invitation
    for pattern in INTENT_PATTERNS["INTERVIEW"]:
        if re.search(pattern, combined):
            snippet = extract_snippet(body, pattern)
            # Check for Calendly or Meeting Link
            link_match = re.search(r"(https?://[^\s]+(?:calendly|zoom|google|calendar)[^\s]+)", body, re.IGNORECASE)
            link_note = f" (Link: {link_match.group(1)[:40]}...)" if link_match else ""
            return (
                "INTERVIEW",
                "Interview Invitation",
                clean_text(f"Recruiter invited to interview{link_note}: '{snippet}'")[:120],
                "📅 Schedule interview slot on calendar"
            )

    # 2. Technical Screening / Assessment
    for pattern in INTENT_PATTERNS["SCREENING"]:
        if re.search(pattern, combined):
            snippet = extract_snippet(body, pattern)
            return (
                "SCREENING",
                "Technical Assessment",
                clean_text(f"Online assessment or take-home requested: '{snippet}'")[:120],
                "📝 Review and complete technical test"
            )

    # 3. Rejection
    for pattern in INTENT_PATTERNS["REJECTED"]:
        if re.search(pattern, combined):
            snippet = extract_snippet(body, pattern)
            return (
                "REJECTED",
                "Rejection Letter",
                clean_text(f"Role closed or candidate not moving forward: '{snippet}'")[:120],
                "📁 Archived"
            )

    # 4. Auto Acknowledgment
    for pattern in INTENT_PATTERNS["AUTO_ACK"]:
        if re.search(pattern, combined):
            snippet = extract_snippet(body, pattern)
            return (
                "SENT",
                "Auto-Acknowledgment",
                clean_text(f"Application received confirmation: '{snippet}'")[:120],
                "⏳ Application acknowledged (Awaiting review)"
            )

    # General Follow-up
    return (
        "SENT",
        "Recruiter Follow-up",
        clean_text(body)[:100] if body else "Recruiter sent message.",
        "💬 Review email reply"
    )


def extract_snippet(body: str, pattern: str) -> str:
    match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return body[:80]
    start = max(0, match.start() - 30)
    end = min(len(body), match.end() + 50)
    snippet = body[start:end].replace("\n", " ").strip()
    return snippet


def fetch_live_imap_emails(creds: Dict[str, str], max_emails: int = 25) -> List[Dict[str, str]]:
    """Connects to real IMAP mailbox and pulls unread/recent messages."""
    server = creds.get("IMAP_SERVER")
    user = creds.get("IMAP_USER")
    password = creds.get("IMAP_PASSWORD")
    if not server or not user or not password:
        return []

    emails_data = []
    try:
        mail = imaplib.IMAP4_SSL(server, int(creds.get("IMAP_PORT", 993)))
        mail.login(user, password)
        mail.select("INBOX")

        # Search for UNSEEN first, then fallback to most recent messages
        status, messages = mail.search(None, 'UNSEEN')
        message_ids = messages[0].split() if status == "OK" and messages[0] else []
        if not message_ids:
            status, messages = mail.search(None, 'ALL')
            if status == "OK" and messages[0]:
                all_ids = messages[0].split()
                message_ids = all_ids[-max_emails:]
        # Take most recent
        for mid in reversed(message_ids[-max_emails:]):
            res, data = mail.fetch(mid, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject
                    subject, encoding = decode_header(msg["Subject"] or "")[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")

                    sender = msg.get("From", "")
                    date_str = msg.get("Date", "")

                    # Extract plain text body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    emails_data.append({
                        "from": sender,
                        "subject": subject,
                        "body": body,
                        "date": date_str
                    })
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"⚠️ [IMAP Listener] Connection check error: {e}")

    return emails_data


def get_simulated_inbox() -> List[Dict[str, str]]:
    """Provides fallback sample emails so the system can run seamlessly even before real IMAP credentials are added."""
    sim_path = BASE_DIR / "inputs" / "simulated_inbox.json"
    if sim_path.exists():
        try:
            with open(sim_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Built-in realistic recruiter replies for initial verification
    return [
        {
            "from": "talent@remotetech.com",
            "subject": "Interview Invitation: Senior Forward Deployed Engineer",
            "body": "Hi Kishor, we reviewed your profile and the KoomAI sub-35ms RAG architecture. We'd love to invite you to speak with our engineering director. Please book a time here: https://calendly.com/remotetech/kishor-30min",
            "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        },
        {
            "from": "recruiting@sidekicklabs.ai",
            "subject": "Thank you for applying to Sidekick Labs",
            "body": "Hi Kishor, we received your application for the Senior AI Engineer role. Our founders are currently reviewing candidate profiles and will be in touch shortly.",
            "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        }
    ]


def sync_emails_and_update_records() -> Dict[str, Any]:
    """
    Main execution function:
      1. Pulls emails (from live IMAP if configured, else simulated).
      2. Matches emails against tracked applications.
      3. Classifies responses and updates application status.
      4. Writes changes to JSON, Markdown board, and Excel tracker.
    """
    _, json_path, md_path = tracker.get_paths()
    apps = tracker.load_board(json_path)
    if not apps:
        return {"updated_count": 0, "message": "No applications on board."}

    creds = load_env_credentials()
    incoming_emails = []
    
    if creds.get("IMAP_SERVER") and creds.get("IMAP_USER") and creds.get("IMAP_PASSWORD"):
        print(f"📬 [Email Watcher] Connecting to live IMAP server ({creds['IMAP_SERVER']})...")
        incoming_emails = fetch_live_imap_emails(creds)
    else:
        print("📬 [Email Watcher] Live IMAP credentials not set in .env; using simulation feed.")
        incoming_emails = get_simulated_inbox()

    updated_count = 0
    updates_log = []

    for msg in incoming_emails:
        sender = msg.get("from", "").lower()
        subject = msg.get("subject", "")
        body = msg.get("body", "")
        msg_date = msg.get("date", datetime.now().isoformat())

        # Match against companies or domains in apps
        for app in apps:
            company = app.get("company", "").lower()
            role = app.get("role", "").lower()

            # Check if company name appears in sender or subject or body
            is_match = False
            if company and (company in sender or company in subject.lower() or company in body.lower()):
                is_match = True
            elif app.get("id", "").lower() in subject.lower():
                is_match = True

            if is_match:
                new_status, resp_cat, summary, next_act = classify_email_intent(subject, body)
                
                # Update app record
                prev_status = app.get("status")
                app["status"] = new_status
                app["response_category"] = resp_cat
                app["response_summary"] = summary
                app["next_action"] = next_act
                app["last_email_date"] = datetime.now().isoformat()
                app["updated_at"] = datetime.now().isoformat()

                if new_status == "INTERVIEW":
                    # Extract interview link or date
                    link_match = re.search(r"(https?://[^\s]+(?:calendly|zoom|meet)[^\s]+)", body, re.IGNORECASE)
                    if link_match:
                        app["interview_date"] = f"Booking link: {link_match.group(1)}"

                note_msg = f"Email received ({resp_cat}): {summary[:60]}"
                notes = app.get("notes")
                if isinstance(notes, list):
                    if note_msg not in notes:
                        notes.append(note_msg)
                elif isinstance(notes, str) and notes:
                    if note_msg not in notes:
                        app["notes"] = f"{notes} | {note_msg}"
                else:
                    app["notes"] = [note_msg]

                updated_count += 1
                updates_log.append({
                    "app_id": app.get("id"),
                    "company": app.get("company"),
                    "previous_status": prev_status,
                    "new_status": new_status,
                    "category": resp_cat
                })
                break

    if updated_count > 0:
        # Save JSON & Markdown
        tracker.save_board(apps, json_path, md_path)
        # Update Excel
        excel_file = excel_tracker.create_or_update_excel(apps)
        print(f"✅ [Email Watcher] Synchronized {updated_count} application status update(s) into Excel ({excel_file}).")
    else:
        # Ensure Excel exists and is fresh
        excel_file = excel_tracker.create_or_update_excel(apps)
        print("ℹ️ [Email Watcher] Checked incoming emails — all application records already up to date.")

    return {
        "updated_count": updated_count,
        "updates": updates_log,
        "excel_path": str(excel_tracker.EXCEL_PATH),
        "board_path": str(md_path)
    }


if __name__ == "__main__":
    res = sync_emails_and_update_records()
    print(f"\nResult: {json.dumps(res, indent=2)}")
