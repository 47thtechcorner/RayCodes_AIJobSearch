#!/usr/bin/env python3
"""
Application Funnel & Tracking System
Adapted from Dossier's application lifecycle and board model (PRD §8).

Manages job applications through standardized stages:
  DRAFT -> SENT -> SCREENING -> INTERVIEW -> OFFER -> ACCEPTED / REJECTED / DECLINED

Maintains:
  - outputs/application_board.json (Structured records)
  - outputs/application_board.md   (Visual Kanban & Funnel Analytics)
"""

import sys
import os
import json
import argparse
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

STAGES = [
    "DRAFT",
    "SENT",
    "SCREENING",
    "INTERVIEW",
    "OFFER",
    "ACCEPTED",
    "REJECTED",
    "DECLINED"
]

STAGE_ICONS = {
    "DRAFT": "📝",
    "SENT": "📨",
    "SCREENING": "🔍",
    "INTERVIEW": "🎯",
    "OFFER": "🎉",
    "ACCEPTED": "🏆",
    "REJECTED": "❌",
    "DECLINED": "✋"
}

FUNNEL_STAGES = ["SENT", "SCREENING", "INTERVIEW", "OFFER", "ACCEPTED"]


def get_paths() -> Tuple[Path, Path, Path]:
    base_dir = Path(__file__).resolve().parent.parent
    out_dir = base_dir / "outputs"
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / "application_board.json"
    md_path = out_dir / "application_board.md"
    return base_dir, json_path, md_path


def load_board(json_path: Path) -> List[Dict[str, Any]]:
    if not json_path.exists():
        # Initialize with sample roles from outputs if available
        base_dir = json_path.parent.parent
        discovered_path = base_dir / "outputs" / "discovered_roles.json"
        initial_apps = []
        if discovered_path.exists():
            try:
                with open(discovered_path, "r", encoding="utf-8") as f:
                    roles = json.load(f)
                    for idx, r in enumerate(roles[:3], 1):
                        initial_apps.append({
                            "id": f"app-{idx}",
                            "company": r.get("company", "Company"),
                            "role": r.get("title", "AI Engineer"),
                            "location": r.get("location", "Remote"),
                            "status": "DRAFT" if idx > 1 else "SENT",
                            "furthest_stage": "DRAFT" if idx > 1 else "SENT",
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "sent_at": datetime.now().isoformat() if idx == 1 else None,
                            "url": r.get("application_url") or r.get("url") or "",
                            "notes": ["Initial application package prepared."],
                            "interview_date": None
                        })
            except Exception:
                pass
        return initial_apps

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_board(apps: List[Dict[str, Any]], json_path: Path, md_path: Path):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=2)
    render_markdown_board(apps, md_path)
    try:
        import excel_tracker
        excel_tracker.create_or_update_excel(apps)
    except Exception as e:
        print(f"Warning: Excel update skipped: {e}")


def render_markdown_board(apps: List[Dict[str, Any]], md_path: Path):
    total = len(apps)
    sent_count = sum(1 for a in apps if a.get("status") != "DRAFT" and a.get("status") != "DECLINED")
    screen_count = sum(1 for a in apps if a.get("status") in ["SCREENING", "INTERVIEW", "OFFER", "ACCEPTED"])
    interview_count = sum(1 for a in apps if a.get("status") in ["INTERVIEW", "OFFER", "ACCEPTED"])
    offer_count = sum(1 for a in apps if a.get("status") in ["OFFER", "ACCEPTED"])

    conversion_screen = round((screen_count / sent_count * 100), 1) if sent_count else 0
    conversion_interview = round((interview_count / sent_count * 100), 1) if sent_count else 0
    conversion_offer = round((offer_count / sent_count * 100), 1) if sent_count else 0

    lines = [
        "# Application Tracking & Funnel Board",
        "",
        "> Track all job applications, callback stages, and interview dates in one place.",
        "",
        "## Funnel Conversion Rates",
        "",
        f"- **Applications Tracked**: `{total}`",
        f"- **Applications Sent**: `{sent_count}`",
        f"- **Screening Rate**: `{screen_count}/{sent_count}` (**{conversion_screen}%**)",
        f"- **Interview Rate**: `{interview_count}/{sent_count}` (**{conversion_interview}%**)",
        f"- **Offer Rate**: `{offer_count}/{sent_count}` (**{conversion_offer}%**)",
        "",
        "---",
        "",
        "## Active Applications Table",
        "",
        "| ID | Company | Role | Location | Status | Sent Date | Interview Date | Notes |",
        "|:---|:---|:---|:---|:---|:---|:---|:---|",
    ]

    for a in apps:
        status_str = f"{STAGE_ICONS.get(a['status'], '')} **{a['status']}**"
        sent_str = a.get("sent_at", "")[:10] if a.get("sent_at") else "—"
        interview_str = a.get("interview_date") or "—"
        notes_str = "; ".join(a.get("notes", []))[:60] if a.get("notes") else "—"
        lines.append(
            f"| `{a.get('id', '')}` | **{a.get('company', '')}** | {a.get('role', '')} | {a.get('location', 'Remote')} | {status_str} | {sent_str} | {interview_str} | {notes_str} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Kanban View by Stage",
        ""
    ])

    for stage in STAGES:
        matching = [a for a in apps if a.get("status") == stage]
        icon = STAGE_ICONS.get(stage, "📌")
        lines.append(f"### {icon} {stage} ({len(matching)})")
        if not matching:
            lines.append("_No applications currently in this stage._\n")
            continue

        for a in matching:
            lines.extend([
                f"- **{a['company']}** — {a['role']} (`{a['id']}`)",
                f"  - Location: {a.get('location', 'Remote')}",
                f"  - Updated: {a.get('updated_at', '')[:10]}",
            ])
            if a.get("interview_date"):
                lines.append(f"  - 📅 **Interview Date**: `{a['interview_date']}`")
            if a.get("url"):
                lines.append(f"  - [Posting Link]({a['url']})")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def list_applications():
    _, json_path, md_path = get_paths()
    apps = load_board(json_path)
    if not apps:
        print("No applications recorded yet. Run 'python3 scripts/tracker.py add' to record one.")
        return

    print(f"\n📋 Application Board ({len(apps)} total):")
    print(f"{'ID':<8} {'Status':<12} {'Company':<25} {'Role':<30} {'Interview'}")
    print("-" * 85)
    for a in apps:
        icon = STAGE_ICONS.get(a['status'], "")
        interview = a.get("interview_date") or "—"
        print(f"{a['id']:<8} {icon} {a['status']:<10} {a['company'][:23]:<25} {a['role'][:28]:<30} {interview}")
    print(f"\n📄 Markdown Board: {md_path}")


def add_application(company: str, role: str, location: str = "Remote", url: str = "", status: str = "DRAFT", note: str = ""):
    base_dir, json_path, md_path = get_paths()
    apps = load_board(json_path)
    
    app_id = f"app-{len(apps) + 1}"
    now_iso = datetime.now().isoformat()
    is_sent = (status.upper() != "DRAFT" and status.upper() != "DECLINED")

    new_app = {
        "id": app_id,
        "company": company,
        "role": role,
        "location": location,
        "status": status.upper(),
        "furthest_stage": status.upper(),
        "created_at": now_iso,
        "updated_at": now_iso,
        "sent_at": now_iso if is_sent else None,
        "url": url,
        "notes": [note] if note else [],
        "interview_date": None
    }
    apps.append(new_app)
    save_board(apps, json_path, md_path)
    print(f"✅ Added {company} ({role}) as `{app_id}` with status **{status.upper()}**.")


def move_application(app_id: str, new_status: str, note: str = "", interview_date: str = ""):
    _, json_path, md_path = get_paths()
    apps = load_board(json_path)
    target = None
    for a in apps:
        if a["id"].lower() == app_id.lower():
            target = a
            break

    if not target:
        print(f"Error: Application ID '{app_id}' not found.")
        return

    new_status = new_status.upper()
    if new_status not in STAGES:
        print(f"Error: Unknown status '{new_status}'. Allowed: {', '.join(STAGES)}")
        return

    prev_status = target["status"]
    target["status"] = new_status
    target["updated_at"] = datetime.now().isoformat()

    if new_status not in ["DRAFT", "DECLINED"] and not target.get("sent_at"):
        target["sent_at"] = datetime.now().isoformat()

    if note:
        target.setdefault("notes", []).append(note)

    if interview_date:
        target["interview_date"] = interview_date

    save_board(apps, json_path, md_path)
    print(f"✅ Application `{app_id}` ({target['company']}) moved: {prev_status} -> **{new_status}**.")


def show_stats():
    _, json_path, _ = get_paths()
    apps = load_board(json_path)
    total = len(apps)
    if total == 0:
        print("No applications recorded yet.")
        return

    counts = {s: sum(1 for a in apps if a.get("status") == s) for s in STAGES}
    sent = sum(1 for a in apps if a.get("status") not in ["DRAFT", "DECLINED"])
    screen = sum(1 for a in apps if a.get("status") in ["SCREENING", "INTERVIEW", "OFFER", "ACCEPTED"])
    interview = sum(1 for a in apps if a.get("status") in ["INTERVIEW", "OFFER", "ACCEPTED"])
    offers = sum(1 for a in apps if a.get("status") in ["OFFER", "ACCEPTED"])

    print(f"\n📊 Career Application Funnel Metrics ({total} total)")
    print("=" * 45)
    for s in STAGES:
        print(f"{STAGE_ICONS.get(s, '')} {s:<12}: {counts[s]}")
    print("-" * 45)
    print(f"Total Sent     : {sent}")
    if sent > 0:
        print(f"Screening Rate : {screen / sent * 100:.1f}%")
        print(f"Interview Rate : {interview / sent * 100:.1f}%")
        print(f"Offer Rate     : {offers / sent * 100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Application Tracker & Funnel Manager")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List all tracked applications")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new job application")
    add_parser.add_argument("--company", required=True, help="Company name")
    add_parser.add_argument("--role", required=True, help="Role title")
    add_parser.add_argument("--location", default="Remote", help="Location or Remote")
    add_parser.add_argument("--url", default="", help="Job posting URL")
    add_parser.add_argument("--status", default="DRAFT", help="Initial status (DRAFT, SENT, etc.)")
    add_parser.add_argument("--note", default="", help="Initial note")

    # move
    move_parser = subparsers.add_parser("move", help="Move application to a new stage")
    move_parser.add_argument("id", help="Application ID (e.g. app-1)")
    move_parser.add_argument("status", help="New stage (SENT, SCREENING, INTERVIEW, OFFER, ACCEPTED, REJECTED)")
    move_parser.add_argument("--note", default="", help="Note about the transition")
    move_parser.add_argument("--interview-date", default="", help="Scheduled interview date")

    # stats
    subparsers.add_parser("stats", help="Show funnel analytics")

    args = parser.parse_args()
    if args.command == "list" or not args.command:
        list_applications()
    elif args.command == "add":
        add_application(args.company, args.role, args.location, args.url, args.status, args.note)
    elif args.command == "move":
        move_application(args.id, args.status, args.note, args.interview_date)
    elif args.command == "stats":
        show_stats()


if __name__ == "__main__":
    main()
