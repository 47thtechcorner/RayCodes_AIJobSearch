#!/usr/bin/env python3
"""
Excel Tracking Engine for 24-Hour Job Search & Application Funnel
Produces and updates a styled, professional Excel workbook:
  outputs/job_applications_tracker.xlsx

Features:
  - Formatted 'Applications Pipeline' worksheet with custom column widths,
    status-based conditional color fills, clickable links, and response notes.
  - Formatted 'Funnel Analytics' worksheet summarizing conversion metrics
    and email response rates.
  - Automatically synchronized with application_board.json.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
EXCEL_PATH = OUTPUTS_DIR / "job_applications_tracker.xlsx"
JSON_BOARD_PATH = OUTPUTS_DIR / "application_board.json"

# Color Palette (Tailored Slate & Modern Corporate)
COLOR_HEADER_BG = "1E293B"      # Dark slate navy
COLOR_HEADER_FG = "FFFFFF"      # White bold text
COLOR_ZEBRA_ROW = "F8FAFC"      # Subtle light gray zebra
COLOR_BORDER = "CBD5E1"         # Slate light border

# Status Fills (Fill Hex, Text Hex)
STATUS_STYLES = {
    "INTERVIEW": ("D1FAE5", "065F46"),  # Soft emerald
    "OFFER":     ("FEF3C7", "92400E"),  # Soft amber / gold
    "ACCEPTED":  ("DCFCE7", "166534"),  # Deep green
    "SCREENING": ("E0F2FE", "0369A1"),  # Soft sky blue
    "SENT":      ("EDE9FE", "5B21B6"),  # Soft violet
    "DRAFT":     ("F1F5F9", "475569"),  # Soft slate
    "REJECTED":  ("FEE2E2", "991B1B"),  # Soft rose / crimson
    "DECLINED":  ("F3F4F6", "374151"),  # Muted gray
}

RESPONSE_STYLES = {
    "Interview Invitation": ("D1FAE5", "065F46"),
    "Technical Assessment": ("E0F2FE", "0369A1"),
    "Recruiter Follow-up":  ("FEF3C7", "92400E"),
    "Rejection Letter":     ("FEE2E2", "991B1B"),
    "Auto-Acknowledgment":  ("F1F5F9", "475569"),
    "Awaiting Reply":       ("FFFFFF", "64748B"),
}


def load_board() -> List[Dict[str, Any]]:
    if not JSON_BOARD_PATH.exists():
        return []
    try:
        with open(JSON_BOARD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading board JSON: {e}")
        return []


def create_or_update_excel(apps: Optional[List[Dict[str, Any]]] = None) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    if apps is None:
        apps = load_board()

    wb = openpyxl.Workbook()
    # Remove default sheet
    default_sheet = wb.active

    # 1. Applications Pipeline Sheet
    ws_pipeline = wb.create_sheet(title="Applications Pipeline")
    build_pipeline_sheet(ws_pipeline, apps)

    # 2. Funnel Analytics Sheet
    ws_analytics = wb.create_sheet(title="Funnel Analytics")
    build_analytics_sheet(ws_analytics, apps)

    # Remove initial empty sheet
    if default_sheet and default_sheet in wb.worksheets:
        wb.remove(default_sheet)

    wb.save(str(EXCEL_PATH))
    return EXCEL_PATH


def build_pipeline_sheet(ws, apps: List[Dict[str, Any]]):
    headers = [
        "App ID",
        "Company",
        "Role / Position",
        "Location / Work Mode",
        "Source",
        "Job URL",
        "Target Resume (ATS Upload)",
        "Recruiter / Contact Email",
        "Fit Score %",
        "Status",
        "Date Discovered",
        "Date Sent",
        "Last Response Date",
        "Response Category",
        "Recruiter Response Summary",
        "Next Action Required",
        "Interview Date",
        "Notes & Activity Log"
    ]

    # Set Title Banner
    ws.merge_cells("A1:R1")
    title_cell = ws["A1"]
    title_cell.value = "🚀 24-Hour AI Career Agent — Live Application & Email Response Tracker"
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # Subtitle / Timestamp
    ws.merge_cells("A2:R2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Candidate: Kishor Kumar Paroi (Principal AI Systems Architect) | Rule: Upload resume_single_column.pdf to Portals | Last Synchronized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    sub_cell.font = Font(name="Calibri", size=10, italic=True, color="64748B")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # Headers in Row 3
    ws.row_dimensions[3].height = 28
    thin_border = Border(
        left=Side(style="thin", color=COLOR_BORDER),
        right=Side(style="thin", color=COLOR_BORDER),
        top=Side(style="thin", color=COLOR_BORDER),
        bottom=Side(style="thin", color=COLOR_BORDER)
    )

    header_font = Font(name="Calibri", size=10, bold=True, color=COLOR_HEADER_FG)
    header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Data Rows
    row_idx = 4
    for a in apps:
        ws.row_dimensions[row_idx].height = 24
        zebra_fill = PatternFill(
            start_color=COLOR_ZEBRA_ROW if row_idx % 2 == 0 else "FFFFFF",
            end_color=COLOR_ZEBRA_ROW if row_idx % 2 == 0 else "FFFFFF",
            fill_type="solid"
        )

        app_id = a.get("id", f"app-{row_idx-3}").upper()
        company = a.get("company", "Unknown")
        role = a.get("role", "AI Engineer")
        location = a.get("location", "Remote")
        source = a.get("source", "Hacker News / YC")
        url = a.get("url", "")
        contact_email = a.get("contact_email") or a.get("email") or "founders@company.com"
        fit_score = a.get("fit_score", 85)
        status = a.get("status", "DRAFT").upper()
        created_at = (a.get("created_at") or "")[:10]
        sent_at = (a.get("sent_at") or "")[:10] if a.get("sent_at") else "—"
        last_response_date = (a.get("last_email_date") or "")[:10] if a.get("last_email_date") else "—"
        
        # Email response parsing info
        resp_category = a.get("response_category")
        if not resp_category:
            if status == "INTERVIEW":
                resp_category = "Interview Invitation"
            elif status == "SCREENING":
                resp_category = "Technical Assessment"
            elif status == "REJECTED":
                resp_category = "Rejection Letter"
            elif status in ["SENT"]:
                resp_category = "Awaiting Reply"
            else:
                resp_category = "Auto-Acknowledgment" if a.get("last_email_date") else "Awaiting Reply"

        resp_summary = a.get("response_summary") or ("Awaiting initial recruiter reply." if status == "SENT" else "Draft prepared and ready for review.")
        
        # Next action calculation
        next_action = a.get("next_action")
        if not next_action:
            if status == "INTERVIEW":
                next_action = "📅 Confirm interview slot on calendar"
            elif status == "SCREENING":
                next_action = "📝 Review take-home screen requirements"
            elif status == "DRAFT":
                next_action = "⚡ 1-Click Review & Send email"
            elif status == "SENT":
                next_action = "⏳ Monitor inbox (Follow-up in 5 days)"
            elif status == "REJECTED":
                next_action = "📁 Archived"
            else:
                next_action = "—"

        interview_date = a.get("interview_date") or "—"
        notes = "; ".join(a.get("notes", [])) if a.get("notes") else "—"

        row_values = [
            app_id,
            company,
            role,
            location,
            source,
            url,
            "resume_single_column.pdf (ATS)",
            contact_email,
            f"{fit_score}%" if isinstance(fit_score, (int, float)) else str(fit_score),
            status,
            created_at,
            sent_at,
            last_response_date,
            resp_category,
            resp_summary,
            next_action,
            interview_date,
            notes
        ]

        for col_idx, val in enumerate(row_values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

            # Default zebra fill
            cell.fill = zebra_fill

            # Centered columns
            if col_idx in [1, 5, 7, 9, 11, 12, 13, 17]:
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Target resume column styling
            if col_idx == 7:
                cell.font = Font(name="Calibri", size=9, bold=True, color="047857")

            # Clickable URL hyperlink
            if col_idx == 6 and url.startswith("http"):
                cell.hyperlink = url
                cell.font = Font(name="Calibri", size=10, color="0284C7", underline="single")

            # Status column styling
            if col_idx == 10:
                s_bg, s_fg = STATUS_STYLES.get(status, ("F1F5F9", "475569"))
                cell.fill = PatternFill(start_color=s_bg, end_color=s_bg, fill_type="solid")
                cell.font = Font(name="Calibri", size=10, bold=True, color=s_fg)
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Response category column styling
            if col_idx == 14 and resp_category in RESPONSE_STYLES:
                r_bg, r_fg = RESPONSE_STYLES[resp_category]
                cell.fill = PatternFill(start_color=r_bg, end_color=r_bg, fill_type="solid")
                cell.font = Font(name="Calibri", size=10, bold=True, color=r_fg)

        row_idx += 1

    # Auto-adjust Column Widths
    col_widths = {
        1: 12,   # App ID
        2: 24,   # Company
        3: 32,   # Role
        4: 25,   # Location
        5: 18,   # Source
        6: 25,   # Job URL
        7: 26,   # Recruiter Email
        8: 12,   # Fit Score
        9: 14,   # Status
        10: 14,  # Date Discovered
        11: 14,  # Date Sent
        12: 18,  # Last Response Date
        13: 24,  # Response Category
        14: 35,  # Response Summary
        15: 32,  # Next Action
        16: 18,  # Interview Date
        17: 35   # Notes
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Freeze panes below headers
    ws.freeze_panes = "A4"


def build_analytics_sheet(ws, apps: List[Dict[str, Any]]):
    total = len(apps)
    sent_count = sum(1 for a in apps if a.get("status") not in ["DRAFT", "DECLINED"])
    screening_count = sum(1 for a in apps if a.get("status") in ["SCREENING", "INTERVIEW", "OFFER", "ACCEPTED"])
    interview_count = sum(1 for a in apps if a.get("status") in ["INTERVIEW", "OFFER", "ACCEPTED"])
    offer_count = sum(1 for a in apps if a.get("status") in ["OFFER", "ACCEPTED"])
    rejected_count = sum(1 for a in apps if a.get("status") == "REJECTED")

    screen_rate = round((screening_count / sent_count * 100), 1) if sent_count else 0
    interview_rate = round((interview_count / sent_count * 100), 1) if sent_count else 0
    offer_rate = round((offer_count / sent_count * 100), 1) if sent_count else 0

    # Header
    ws.merge_cells("A1:F1")
    title_cell = ws["A1"]
    title_cell.value = "📊 Job Application Funnel & Response Conversion Metrics"
    title_cell.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    thin_border = Border(
        left=Side(style="thin", color=COLOR_BORDER),
        right=Side(style="thin", color=COLOR_BORDER),
        top=Side(style="thin", color=COLOR_BORDER),
        bottom=Side(style="thin", color=COLOR_BORDER)
    )

    # Funnel Table
    headers_f = ["Funnel Stage", "Count", "Conversion Rate %", "Industry Benchmark %"]
    for col_idx, h in enumerate(headers_f, 1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[3].height = 24

    metrics_rows = [
        ("Total Tracked Opportunities", total, "100%", "—"),
        ("Applications Sent / Outreached", sent_count, f"{round(sent_count/total*100, 1) if total else 0}%", "20 - 30%"),
        ("Screening Callbacks Received", screening_count, f"{screen_rate}%", "10 - 15%"),
        ("Technical & Founder Interviews", interview_count, f"{interview_rate}%", "5 - 8%"),
        ("Final Job Offers", offer_count, f"{offer_rate}%", "1 - 3%"),
        ("Rejections / Closed Roles", rejected_count, f"{round(rejected_count/sent_count*100, 1) if sent_count else 0}%", "—")
    ]

    for idx, (stage, count, rate, bench) in enumerate(metrics_rows, 4):
        ws.row_dimensions[idx].height = 22
        ws.cell(row=idx, column=1, value=stage).border = thin_border
        ws.cell(row=idx, column=2, value=count).border = thin_border
        ws.cell(row=idx, column=3, value=rate).border = thin_border
        ws.cell(row=idx, column=4, value=bench).border = thin_border

        ws.cell(row=idx, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=idx, column=3).alignment = Alignment(horizontal="center")
        ws.cell(row=idx, column=4).alignment = Alignment(horizontal="center")

    # Email Response Breakdown
    ws.cell(row=12, column=1, value="Email Response Category Breakdown").font = Font(name="Calibri", size=11, bold=True, color="1E293B")
    
    headers_r = ["Response Category", "Count", "Percentage %"]
    for col_idx, h in enumerate(headers_r, 1):
        cell = ws.cell(row=13, column=col_idx, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="475569", end_color="475569", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # Count response categories
    cat_counts = {}
    for a in apps:
        cat = a.get("response_category")
        if not cat:
            cat = "Interview Invitation" if a.get("status") == "INTERVIEW" else ("Awaiting Reply" if a.get("status") == "SENT" else "Draft Stage")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    r_idx = 14
    for cat, c in cat_counts.items():
        ws.row_dimensions[r_idx].height = 20
        pct = f"{round(c/total*100, 1)}%" if total else "0%"
        ws.cell(row=r_idx, column=1, value=cat).border = thin_border
        ws.cell(row=r_idx, column=2, value=c).border = thin_border
        ws.cell(row=r_idx, column=3, value=pct).border = thin_border
        ws.cell(row=r_idx, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=r_idx, column=3).alignment = Alignment(horizontal="center")
        r_idx += 1

    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 24
    ws.column_dimensions["D"].width = 24


def sync_board_to_excel() -> str:
    path = create_or_update_excel()
    return str(path)


if __name__ == "__main__":
    out_file = sync_board_to_excel()
    print(f"✅ Excel Application Tracker updated successfully at: {out_file}")
