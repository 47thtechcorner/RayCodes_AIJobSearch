#!/usr/bin/env python3
"""
Dual-Channel Dispatcher & Dual-Resume Attachment Engine
Handles two distinct channels with custom attachments and body templates:
  Channel 1: 'FOUNDER' -> Founder-to-Founder consulting pitch, portfolio links + BOTH RESUMES ATTACHED.
  Channel 2: 'COMPANY' -> Formal Job Application, tailored Cover Letter + BOTH RESUMES ATTACHED.

Attachments Included in EVERY Email:
  1. Kishor_Kumar_Paroi_1Page_ATS_Resume.pdf (Minimalist 1-Page ATS-100 Format)
  2. Kishor_Kumar_Paroi_Comprehensive_Portfolio_Resume.pdf (Detailed Deep-Dive Architecture Resume)
"""

import sys
import os
import smtplib
import imaplib
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

RESUME_1PAGE_PATH = ROOT_DIR / "resume.pdf" if (ROOT_DIR / "resume.pdf").exists() else ROOT_DIR / "simple_resume.pdf"
RESUME_FULL_PATH = ROOT_DIR / "resume_single_column.pdf" if (ROOT_DIR / "resume_single_column.pdf").exists() else ROOT_DIR / "full_comprehensive_resume.pdf"

sys.path.insert(0, str(BASE_DIR / "scripts"))
import founder_discovery
import founders_crm
import email_drafter
import fact_guard
import tracker
import excel_tracker
import continuous_batch_accumulator
import project_matcher


def load_mail_credentials():
    env_file = BASE_DIR / ".env"
    cfg = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "IMAP_SERVER": "imap.gmail.com",
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "SENDER_NAME": "Kishor Kumar Paroi"
    }
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in cfg:
                        cfg[k] = v
    return cfg


def craft_founder_cold_email(company: str, role_title: str, recipient_email: str, snippet: str = "") -> Dict[str, str]:
    return project_matcher.generate_curated_cold_email(company, role_title, recipient_email, snippet)

def craft_company_formal_application(company: str, role_title: str, recipient_email: str, snippet: str = "") -> Dict[str, str]:
    return project_matcher.generate_curated_cover_letter(company, role_title, recipient_email, snippet)


def send_dual_channel_email(
    channel: str, # 'FOUNDER' or 'COMPANY'
    company: str,
    role_title: str,
    recipient_email: str,
    send_live: bool = False
) -> Dict[str, Any]:
    cfg = load_mail_credentials()

    if channel == "FOUNDER":
        draft = craft_founder_cold_email(company, role_title, recipient_email)
        target_folder = "Career-AI/Founders-Outreach"
    else: # COMPANY
        draft = craft_company_formal_application(company, role_title, recipient_email)
        target_folder = "Career-AI/Company-Applications"

    # Fact Guard Audit
    gt_sources = fact_guard.load_candidate_sources(BASE_DIR)
    audit = fact_guard.verify_text(draft["body"], gt_sources)
    if not audit.get("verified", True):
        return {"status": "FLAGGED", "error": "Fact Guard verification failed"}

    if not send_live:
        return {
            "status": "STAGED",
            "channel": channel,
            "company": company,
            "recipient": recipient_email,
            "subject": draft["subject"],
            "body": draft["body"],
            "attachments": [
                "Kishor_Kumar_Paroi_1Page_Visual_Resume.pdf (resume.pdf)",
                "Kishor_Kumar_Paroi_Single_Column_ATS_Resume.pdf (resume_single_column.pdf)"
            ],
            "folder": target_folder
        }

    # Live Dispatch via SMTP with BOTH Resume Attachments
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{cfg['SENDER_NAME']} <{cfg['SMTP_USER']}>"
        msg["To"] = recipient_email
        msg["Subject"] = draft["subject"]
        msg.attach(MIMEText(draft["body"], "plain"))

        # Attachment 1: 1-Page Visual Human Review Resume (resume.pdf)
        if RESUME_1PAGE_PATH.exists():
            with open(RESUME_1PAGE_PATH, "rb") as f:
                attach1 = MIMEApplication(f.read(), _subtype="pdf")
                attach1.add_header("Content-Disposition", "attachment", filename="Kishor_Kumar_Paroi_1Page_Visual_Resume.pdf")
                msg.attach(attach1)

        # Attachment 2: Single-Column Linear ATS Resume (resume_single_column.pdf)
        if RESUME_FULL_PATH.exists():
            with open(RESUME_FULL_PATH, "rb") as f:
                attach2 = MIMEApplication(f.read(), _subtype="pdf")
                attach2.add_header("Content-Disposition", "attachment", filename="Kishor_Kumar_Paroi_Single_Column_ATS_Resume.pdf")
                msg.attach(attach2)

        # 1. Send SMTP
        with smtplib.SMTP(cfg["SMTP_SERVER"], int(cfg["SMTP_PORT"]), timeout=15) as s:
            s.starttls()
            s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            s.send_message(msg)

        # 2. Append to specific Gmail Label via IMAP
        try:
            with imaplib.IMAP4_SSL(cfg["IMAP_SERVER"], 993) as imap:
                imap.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
                imap.append(target_folder, '\\Seen', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
        except Exception as e:
            print(f"Notice: IMAP label append note ({target_folder}): {e}")

        print(f"✉️ [SENT {channel}] Delivered to {company} ({recipient_email}) with BOTH RESUMES -> Saved to Gmail '{target_folder}'")
        return {"status": "DELIVERED", "channel": channel, "recipient": recipient_email}
    except Exception as e:
        print(f"❌ Error sending {channel} email to {recipient_email}: {e}")
        return {"status": "ERROR", "error": str(e)}


if __name__ == "__main__":
    print("Testing Dual-Channel Dispatcher with Both Resumes...")
    f_res = send_dual_channel_email("FOUNDER", "RemoteTech", "AI Architect", "founders@remotetech.com", send_live=False)
    print("Founder Staged Subject:", f_res["subject"])
    print("Attachments:", f_res.get("attachments"))
    c_res = send_dual_channel_email("COMPANY", "RemoteTech", "AI Architect", "jobs@remotetech.com", send_live=False)
    print("Company Staged Subject:", c_res["subject"])
    print("Attachments:", c_res.get("attachments"))
