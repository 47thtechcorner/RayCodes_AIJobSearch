#!/usr/bin/env python3
"""
Founders CRM & Cold Mail Delivery Tracker
Manages:
  1. Elite High-Converting Cold Mail Template (incorporating full resume technical stack & founder capability).
  2. Separate dedicated Excel worksheet: 'Founders Outreach CRM' in job_applications_tracker.xlsx
  3. Structured JSON export: outputs/founders_outreach_crm.json
  4. Real-time Delivery Status tracking:
     - 'DRAFT' -> 'STAGED' -> 'DELIVERED (SMTP)'
     - Inbound Reply Tracking: 'Awaiting Reply' -> 'REPLIED (Interview / Screen / Offer)'
"""

import sys
import os
import json
import time
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
JSON_CRM_PATH = OUTPUTS_DIR / "founders_outreach_crm.json"
EXCEL_PATH = OUTPUTS_DIR / "job_applications_tracker.xlsx"

sys.path.insert(0, str(BASE_DIR / "scripts"))
import founder_discovery
import email_drafter
import fact_guard
import tracker
import project_matcher


def get_high_converting_cold_mail(company: str, role_title: str, recipient_email: str, profile: Dict[str, Any], snippet: str = "") -> Dict[str, str]:
    return project_matcher.generate_curated_cold_email(company, role_title, recipient_email, snippet)


def load_smtp_config() -> Dict[str, str]:
    env_file = BASE_DIR / ".env"
    cfg = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "SENDER_NAME": "Kishor Kumar Paroi"
    }
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in cfg:
                        cfg[k] = v
    return cfg


def load_crm_records() -> List[Dict[str, Any]]:
    if JSON_CRM_PATH.exists():
        try:
            with open(JSON_CRM_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_crm_records(records: List[Dict[str, Any]]):
    with open(JSON_CRM_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def sync_crm_to_excel(records: List[Dict[str, Any]]):
    """Writes styled 'Founders Outreach CRM' worksheet into job_applications_tracker.xlsx."""
    if not EXCEL_PATH.exists():
        wb = openpyxl.Workbook()
    else:
        wb = openpyxl.load_workbook(EXCEL_PATH)

    sheet_name = "Founders Outreach CRM"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]
    ws = wb.create_sheet(title=sheet_name)

    # Styles
    navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    gold_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    # Title Block
    ws.merge_cells("A1:K1")
    ws["A1"] = "TECH FOUNDERS & LEAD OUTREACH CRM (AUTOMATED 24/7 DISPATCH & TRACKER)"
    ws["A1"].font = title_font
    ws["A1"].fill = navy_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 35

    ws.merge_cells("A2:K2")
    ws["A2"] = f"Total Contacts: {len(records)} | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Candidate: Kishor Kumar Paroi (RUET CSE / Founder@KoomAI)"
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="94A3B8")
    ws["A2"].fill = navy_fill
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    # Headers
    headers = [
        "CRM ID", "Company", "Role / Opportunity", "Target Email",
        "Delivery Status", "Mail Sent?", "Dispatch Date",
        "Reply Received?", "Reply Intent", "One-Click Mailto", "Notes & Activity"
    ]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.font = white_bold
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 26

    # Data Rows
    for row_idx, r in enumerate(records, 4):
        delivery_status = r.get("delivery_status", "STAGED")
        mail_sent = "YES" if r.get("mail_sent") else "NO"
        reply_got = "YES" if r.get("reply_received") else "Awaiting"

        row_bg = "FFFFFF"
        if r.get("reply_received"):
            row_bg = "D1FAE5"  # Soft emerald
        elif r.get("mail_sent"):
            row_bg = "F0FDF4"  # Subtle green
        elif delivery_status == "STAGED":
            row_bg = "FEF3C7"  # Soft amber

        fill = PatternFill(start_color=row_bg, end_color=row_bg, fill_type="solid")

        vals = [
            r.get("crm_id", f"CRM-{row_idx-3}"),
            r.get("company", ""),
            r.get("role", ""),
            r.get("email", ""),
            delivery_status,
            mail_sent,
            r.get("dispatch_date", "—"),
            reply_got,
            r.get("reply_intent", "None yet"),
            r.get("mailto_url", ""),
            r.get("notes", "")
        ]

        for col_idx, v in enumerate(vals, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=v)
            cell.font = data_font
            cell.fill = fill
            cell.border = thin_border
            if col_idx in [1, 5, 6, 7, 8]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            if col_idx == 10 and str(v).startswith("mailto:"):
                cell.value = "✉️ Send Email"
                cell.hyperlink = v
                cell.font = Font(name="Calibri", size=10, color="2563EB", underline="single")

        ws.row_dimensions[row_idx].height = 20

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(EXCEL_PATH)
    print(f"📊 [CRM Excel Sync] Updated 'Founders Outreach CRM' worksheet in {EXCEL_PATH}")


def run_crm_discovery_and_dispatch(batch_count: int = 20, send_live: bool = False) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"💼 [Founders CRM] Sourcing Founders & Managing Cold Outreach...")
    print(f"{'='*70}")

    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)
    profile = email_drafter.load_candidate_profile(BASE_DIR)
    smtp_cfg = load_smtp_config()

    existing_crm = load_crm_records()
    crm_by_company = {r["company"].lower(): r for r in existing_crm}

    new_dispatches = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    smtp_conn = None
    if send_live and smtp_cfg.get("SMTP_USER") and smtp_cfg.get("SMTP_PASSWORD"):
        try:
            smtp_conn = smtplib.SMTP(smtp_cfg["SMTP_SERVER"], int(smtp_cfg["SMTP_PORT"]), timeout=15)
            smtp_conn.starttls()
            smtp_conn.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASSWORD"])
            print(f"✅ Connected to Gmail SMTP as {smtp_cfg['SMTP_USER']}!")
        except Exception as e:
            print(f"⚠️ SMTP Connection error: {e}. Will stage messages.")
            smtp_conn = None

    for app in board:
        if new_dispatches >= batch_count:
            break

        comp = app.get("company", "").strip()
        role = app.get("role", "AI Engineer").strip()
        url = app.get("url", "")
        snippet = " ".join(app.get("notes", [])) if isinstance(app.get("notes"), list) else str(app.get("notes", ""))

        if not comp or comp.lower() in crm_by_company:
            continue

        founder_email = founder_discovery.discover_contact_email(comp, url, snippet)
        pitch = get_high_converting_cold_mail(comp, role, founder_email, profile)

        mail_sent = False
        delivery_status = "STAGED"
        dispatch_date = now_str

        # Zero-Bounce Guard: Validate domain and MX records
        is_valid, validation_reason = founder_discovery.validate_recipient_email(founder_email, comp)
        if not is_valid:
            print(f"🛑 [Zero-Bounce Guard] Blocked dispatch for {comp} ({founder_email}): {validation_reason}")
            delivery_status = f"BLOCKED: {validation_reason}"
        elif smtp_conn:
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{smtp_cfg['SENDER_NAME']} <{smtp_cfg['SMTP_USER']}>"
                msg["To"] = founder_email
                msg["Subject"] = pitch["subject"]
                msg.attach(MIMEText(pitch["body"], "plain"))

                # Attach BOTH Resumes (Primary Visual 1-Page + Single Column ATS)
                from email.mime.application import MIMEApplication
                p1 = BASE_DIR.parent / "resume.pdf" if (BASE_DIR.parent / "resume.pdf").exists() else BASE_DIR.parent / "simple_resume.pdf"
                p2 = BASE_DIR.parent / "resume_single_column.pdf" if (BASE_DIR.parent / "resume_single_column.pdf").exists() else BASE_DIR.parent / "full_comprehensive_resume.pdf"
                if p1.exists():
                    with open(p1, "rb") as fp:
                        a1 = MIMEApplication(fp.read(), _subtype="pdf")
                        a1.add_header("Content-Disposition", "attachment", filename="Kishor_Kumar_Paroi_1Page_Visual_Resume.pdf")
                        msg.attach(a1)
                if p2.exists():
                    with open(p2, "rb") as fp:
                        a2 = MIMEApplication(fp.read(), _subtype="pdf")
                        a2.add_header("Content-Disposition", "attachment", filename="Kishor_Kumar_Paroi_Single_Column_ATS_Resume.pdf")
                        msg.attach(a2)

                smtp_conn.send_message(msg)
                mail_sent = True
                delivery_status = "DELIVERED (SMTP)"
                print(f"✉️ [LIVE SMTP SENT] {comp} -> {founder_email}")
                app["status"] = "SENT"
                app["response_category"] = "Awaiting Reply"
            except Exception as e:
                print(f"⚠️ Failed to send to {founder_email}: {e}")
                delivery_status = "STAGED"

        crm_record = {
            "crm_id": f"CRM-{len(existing_crm) + 1:04d}",
            "company": comp,
            "role": role,
            "email": founder_email,
            "delivery_status": delivery_status,
            "mail_sent": mail_sent,
            "dispatch_date": dispatch_date,
            "reply_received": False,
            "reply_intent": "Awaiting Reply",
            "mailto_url": pitch["mailto_url"],
            "notes": f"Verified resume architecture pitch tailored to {comp}."
        }

        existing_crm.append(crm_record)
        crm_by_company[comp.lower()] = crm_record
        new_dispatches += 1

    if smtp_conn:
        try:
            smtp_conn.quit()
        except Exception:
            pass

    save_crm_records(existing_crm)
    sync_crm_to_excel(existing_crm)
    tracker.save_board(board, json_path, md_path)

    summary = {
        "total_crm_contacts": len(existing_crm),
        "new_added": new_dispatches,
        "json_path": str(JSON_CRM_PATH),
        "excel_path": str(EXCEL_PATH)
    }
    print(f"\n✅ Founders CRM Processed! Total Contacts: {len(existing_crm)} (New added: {new_dispatches})")
    print(f"📁 Exported JSON: {JSON_CRM_PATH.relative_to(BASE_DIR)}")
    print(f"📊 Excel Sheet: 'Founders Outreach CRM' in {EXCEL_PATH.name}")
    print(f"{'='*70}\n")
    return summary


if __name__ == "__main__":
    live = "--live" in sys.argv
    count = 20
    for arg in sys.argv[1:]:
        if arg.isdigit():
            count = int(arg)
    run_crm_discovery_and_dispatch(batch_count=count, send_live=live)
