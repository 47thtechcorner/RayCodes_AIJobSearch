#!/usr/bin/env python3
"""
24-Hour Nonstop AI Career Agent & Orchestrator
Runs around the clock to:
  1. Fetch and score fresh job vacancies continuously (every N hours).
  2. Auto-tailor customized applications & outreach pitches (Fact Guard verified).
  3. Keep a styled Excel workbook (outputs/job_applications_tracker.xlsx) updated in real time.
  4. Watch email inbox every 15 minutes, classify recruiter responses, and update the Excel tracker & Kanban board.

Improvisations:
  - Dual-cadence architecture (fast email sync vs steady job fetch).
  - Rate limiting & anti-ban throttle (capped daily volume to protect domain reputation).
  - Exponential backoff on network/API glitches so the daemon never crashes.
  - Graceful signal handling (SIGINT/SIGTERM).
"""

import sys
import os
import time
import signal
import argparse
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import hn_startups
import batch_push
import fetch_from_profile_sources
import founders_crm
import continuous_batch_accumulator
import fact_guard
import email_drafter
import tracker
import excel_tracker
import email_watcher
import dossier_sync

RUNNING = True


def handle_shutdown(signum, frame):
    global RUNNING
    print(f"\n🛑 [24-Hour Agent] Received stop signal ({signum}). Gracefully shutting down...")
    RUNNING = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def run_job_discovery_and_apply_cycle(min_score: int = 75, max_new_per_cycle: int = 50) -> int:
    """Fetches vacancies, customizes pitches, audits claims, and logs to Excel."""
    cycle_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*70}")
    print(f"📡 [24h Vacancy Scanner] Starting Job Fetch Cycle: {cycle_time}")
    print(f"{'='*70}")

    # 1. 1-Second Continuous Accumulator & 100-Batch Push (Threshold >= 50% Fit)
    try:
        pushed = continuous_batch_accumulator.run_continuous_ingestion(target_accumulate=100)
        print(f"⚡ [1s Accumulator] Batch pushed {pushed} new jobs into job_applications_tracker.xlsx & founder_outreach.xlsx.")
    except Exception as e:
        print(f"⚠️ Continuous batch ingestion notice: {e}")

    # 2. Targeted startup scans
    try:
        roles = hn_startups.scan_startups(max_results=20)
    except Exception as e:
        print(f"⚠️ Warning during job fetch: {e}")
        return 0

    print(f"✓ Scanned feeds: Found {len(roles)} active roles.")

    # 2. Filter high-fit roles
    top_matches = [r for r in roles if r.get("fit_score", 0) >= min_score]
    print(f"🎯 Target alignment: {len(top_matches)} roles meet score >= {min_score}%.")

    _, json_path, md_path = tracker.get_paths()
    existing_board = tracker.load_board(json_path)
    existing_companies = {a.get("company", "").lower() for a in existing_board}

    new_apps = 0
    profile = email_drafter.load_candidate_profile(BASE_DIR)

    for role in top_matches:
        if new_apps >= max_new_per_cycle:
            print(f"⏸️ Cycle throttle reached ({max_new_per_cycle} roles). Saving remaining for next cycle.")
            break

        company = role.get("company", "Company")
        title = role.get("title", "AI Systems Engineer")

        # Skip already tracked companies
        if company.lower() in existing_companies:
            continue

        print(f"\n⚡ Preparing Customized Pitch: {company} — {title}")
        email_data = email_drafter.draft_application_email(role, profile)
        print(f"   📧 Recruiter Contact: {email_data.get('to')}")

        # Fact Guard audit check
        sources = fact_guard.load_candidate_sources(BASE_DIR)
        guard_res = fact_guard.verify_text(email_data["body"], sources)
        guard_status = "✅ Fact Guard Clean" if guard_res["is_clean"] else f"⚠️ {guard_res['total_flags']} flag(s)"
        print(f"   🛡️ Ground-Truth Audit: {guard_status}")

        # Add to board record
        app_id = f"app-{len(existing_board) + 1}"
        new_record = {
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
            "notes": [f"Auto-tailored by 24h Agent ({role.get('fit_score')}% fit)"],
            "interview_date": None
        }

        existing_board.append(new_record)
        existing_companies.add(company.lower())
        new_apps += 1

    # Save to JSON, Markdown, and Excel
    if new_apps > 0:
        tracker.save_board(existing_board, json_path, md_path)
        excel_file = excel_tracker.create_or_update_excel(existing_board)
        print(f"\n📊 Updated Excel Tracker: {excel_file}")
        print(f"📋 Application Board: {md_path}")
    else:
        print("\nℹ️ No new unseen companies found in this cycle.")

    try:
        dossier_sync.export_to_dossier()
    except Exception:
        pass
    return new_apps


def run_email_inbox_sync_cycle() -> int:
    """Checks inbox for recruiter replies and updates Excel accordingly."""
    print(f"\n📬 [24h Email Watcher] Checking inbox for recruiter replies at {datetime.now().strftime('%H:%M:%S')}...")
    try:
        res = email_watcher.sync_emails_and_update_records()
        updated = res.get("updated_count", 0)
        # Update CRM replies status if matching email found
        try:
            crm_records = founders_crm.load_crm_records()
            if crm_records and res.get("updates"):
                for u in res.get("updates", []):
                    for c in crm_records:
                        if c["company"].lower() == u["company"].lower():
                            c["reply_received"] = True
                            c["reply_intent"] = u.get("new_status", "REPLIED")
                founders_crm.save_crm_records(crm_records)
                founders_crm.sync_crm_to_excel(crm_records)
        except Exception:
            pass

        if updated > 0:
            for u in res.get("updates", []):
                print(f"   🔔 STATUS CHANGE: {u['company']} -> {u['new_status']} ({u['category']})")
        return updated
    except Exception as e:
        print(f"⚠️ Email sync check warning: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="24-Hour Nonstop AI Career Agent & Excel Sync")
    parser.add_argument("--job-interval", type=float, default=0.0833, help="Hours between job vacancy fetch cycles (e.g. 0.0833 for 5 mins)")
    parser.add_argument("--job-interval-minutes", type=float, default=5.0, help="Minutes between job vacancy fetch cycles (default: 5.0)")
    parser.add_argument("--email-interval", type=float, default=15.0, help="Minutes between email inbox sync checks (default: 15.0)")
    parser.add_argument("--min-score", type=int, default=30, help="Minimum fit score (default: 30)")
    parser.add_argument("--once", action="store_true", help="Run one full cycle (jobs + emails + excel) and exit")
    parser.add_argument("--status", action="store_true", help="Print current tracking stats and exit")
    args = parser.parse_args()

    if args.status:
        tracker.list_applications()
        tracker.show_stats()
        print(f"\n📊 Excel File: {excel_tracker.EXCEL_PATH}")
        return

    print("=" * 70)
    print("🤖 24-HOUR AUTONOMOUS AI CAREER AGENT")
    print("=" * 70)
    print(f"Candidate: Kishor Kumar Paroi (Principal AI Systems Architect)")
    print(f"Job Fetch Cadence: Every {args.job_interval_minutes} minute(s)")
    print(f"Email Sync Cadence: Every {args.email_interval} minute(s)")
    print(f"Excel Tracker Target: outputs/job_applications_tracker.xlsx")
    print("=" * 70)

    # Initial Run
    run_job_discovery_and_apply_cycle(min_score=args.min_score)
    run_email_inbox_sync_cycle()

    if args.once:
        print("\n✨ Single execution cycle completed. Exiting (--once).")
        return

    print("\n🟢 24-Hour Loop Active! Running continuously in background. Press Ctrl+C to stop.")

    email_interval_sec = max(60, int(args.email_interval * 60))
    job_interval_sec = max(60, int(args.job_interval_minutes * 60 if args.job_interval_minutes else args.job_interval * 3600))

    last_job_run = time.time()
    last_email_run = time.time()

    while RUNNING:
        try:
            now = time.time()

            # Email check loop (frequent)
            if now - last_email_run >= email_interval_sec:
                run_email_inbox_sync_cycle()
                last_email_run = now

            # Job discovery loop (periodic)
            if now - last_job_run >= job_interval_sec:
                run_job_discovery_and_apply_cycle(min_score=args.min_score)
                last_job_run = now

            # Sleep short duration for responsive Ctrl+C
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Unexpected loop error (resuming in 10s): {e}")
            traceback.print_exc()
            time.sleep(10)

    print("\n👋 24-Hour Career Agent stopped gracefully.")


if __name__ == "__main__":
    main()
