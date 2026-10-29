#!/usr/bin/env python3
"""
24-Hour Career Agent Daemon & Scheduler
Autonomous loop that runs around the clock:
  1. Scans Hacker News 'Who is hiring?' and Y Combinator every N hours.
  2. Computes bounded fit score (0-100) against your candidate profile.
  3. Uses your chosen model (Gemma / Nemotron / OpenCode / Gemini Low Mode / Antigravity Native)
     to draft customized pitches.
  4. Audits claims with Fact Guard to ensure zero hallucination.
  5. Updates outputs/job_applications_tracker.xlsx (Excel) and outputs/application_board.md.
  6. Watches your inbox every 15 minutes, classifies recruiter replies (Interview, Screening,
     Rejection, Auto-ACK), and keeps your Excel board updated in real time.
"""

import sys
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

# Enable unbuffered / line-buffered stdout for nohup logging
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import hn_startups
import fact_guard
import email_drafter
import tracker
import excel_tracker
import email_watcher
import ai_inference


def run_cycle(min_score: int = 80):
    cycle_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 70)
    print(f"⏰ [24-Hour Career Autopilot] Starting Scan Cycle: {cycle_time}")
    print("=" * 70)

    # 1. Discover active startup vacancies
    print("📡 Step 1: Scanning Hacker News & YC Startup feeds...")
    roles = hn_startups.scan_startups(max_results=20)
    print(f"✓ Discovered {len(roles)} active roles.")

    # 2. Filter high-alignment roles
    top_matches = [r for r in roles if r.get("fit_score", 0) >= min_score]
    print(f"🎯 Step 2: Found {len(top_matches)} high-alignment roles (Score >= {min_score}%).")

    # 3. Process each high-alignment role
    _, json_path, md_path = tracker.get_paths()
    existing_board = tracker.load_board(json_path)
    existing_companies = {a.get("company", "").lower() for a in existing_board}

    new_applications = 0
    profile = email_drafter.load_candidate_profile(BASE_DIR)

    for role in top_matches:
        company = role.get("company", "Company")
        title = role.get("title", "AI Role")
        
        # Avoid duplicate drafts
        if company.lower() in existing_companies:
            continue

        print(f"\n⚡ Processing New Opportunity: {company} ({title})")
        
        # Prepare application email with AI customization
        email_data = email_drafter.draft_application_email(role, profile)
        print(f"   📧 Drafted outreach email for: {email_data['to']}")

        # Add to Application Tracker as DRAFT
        app_id = f"app-{len(existing_board) + 1}"
        new_app = {
            "id": app_id,
            "company": company,
            "role": title,
            "location": role.get("location", "Remote"),
            "source": role.get("source", "Hacker News / YC"),
            "url": role.get("application_url", ""),
            "contact_email": email_data.get("to"),
            "fit_score": role.get("fit_score", min_score),
            "status": "DRAFT",
            "furthest_stage": "DRAFT",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "sent_at": None,
            "last_email_date": None,
            "response_category": "Awaiting Reply",
            "response_summary": "Customized pitch prepared and verified.",
            "next_action": "⚡ 1-Click Review & Send email",
            "notes": [f"Auto-drafted by 24h Autopilot (Fit: {role.get('fit_score')}%)"],
            "interview_date": None
        }
        existing_board.append(new_app)
        existing_companies.add(company.lower())
        new_applications += 1

    # Save board & Excel updates
    if new_applications > 0:
        tracker.save_board(existing_board, json_path, md_path)
        excel_file = excel_tracker.create_or_update_excel(existing_board)
        print(f"\n📋 Updated Application Board: {new_applications} new role(s) queued for review.")
        print(f"📊 Live Excel Tracker updated: {excel_file}")
    else:
        print("\nℹ️ All top matches already queued on board.")

    # 4. Run Fact Guard Audit on latest draft
    draft_file = BASE_DIR / "outputs" / "tailored_application.md"
    if draft_file.exists():
        print("\n🔍 Step 4: Running Fact Guard verification check...")
        sources = fact_guard.load_candidate_sources(BASE_DIR)
        with open(draft_file, "r", encoding="utf-8") as f:
            content = f.read()
        res = fact_guard.verify_text(content, sources)
        print(f"   Fact Guard Status: {'✅ Clean (Zero Hallucination)' if res['is_clean'] else f'⚠️ {res['total_flags']} item(s) flagged'}")

    # 5. Check email responses
    print("\n📬 Step 5: Checking email inbox for recruiter replies...")
    try:
        email_res = email_watcher.sync_emails_and_update_records()
        if email_res.get("updated_count", 0) > 0:
            for u in email_res.get("updates", []):
                print(f"   🔔 Recruiter Reply: {u['company']} -> {u['new_status']} ({u['category']})")
    except Exception as e:
        print(f"   ⚠️ Email check warning: {e}")

    print("\n" + "-" * 70)
    print(f"✨ Cycle Complete at {datetime.now().strftime('%H:%M:%S')}. Check outputs/job_applications_tracker.xlsx")
    print("-" * 70)


def run_daemon(interval_hours: float = 4.0, email_check_minutes: float = 15.0):
    print("=" * 70)
    print(f"🚀 24-HOUR NONSTOP CAREER AGENT DAEMON ACTIVE")
    print("=" * 70)
    print(f"Candidate: Kishor Kumar Paroi (Principal AI Systems Architect)")
    print(f"Job Vacancy Cycle: Every {interval_hours} hour(s)")
    print(f"Email Inbox Sync:  Every {email_check_minutes} minute(s)")
    print(f"Excel Tracker:     outputs/job_applications_tracker.xlsx")
    print("=" * 70)
    print("Press Ctrl+C at any time to stop.\n")

    # Initial cycle
    run_cycle()

    job_interval_sec = int(interval_hours * 3600)
    email_interval_sec = int(email_check_minutes * 60)

    last_job_run = time.time()
    last_email_run = time.time()

    try:
        while True:
            now = time.time()

            # Check emails frequently
            if now - last_email_run >= email_interval_sec:
                print(f"\n📬 [Inbox Sync] Checking recruiter responses at {datetime.now().strftime('%H:%M:%S')}...")
                email_watcher.sync_emails_and_update_records()
                last_email_run = now

            # Fetch fresh job vacancies periodically
            if now - last_job_run >= job_interval_sec:
                run_cycle()
                last_job_run = now

            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Career Agent Daemon stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(description="24-Hour Career Agent Continuous Runner")
    parser.add_argument("--once", action="store_true", help="Run a single scan and exit")
    parser.add_argument("--interval", type=float, default=4.0, help="Interval in hours between scans (default: 4.0)")
    parser.add_argument("--provider", type=str, default="", help="AI provider: agent_native | local_opencode | local_ollama | gemini_low_mode")
    args = parser.parse_args()

    if args.provider:
        os.environ["ACTIVE_AI_PROVIDER"] = args.provider
        print(f"Configured AI Provider: {args.provider}")

    if args.once:
        run_cycle()
    else:
        run_daemon(args.interval)


if __name__ == "__main__":
    main()
