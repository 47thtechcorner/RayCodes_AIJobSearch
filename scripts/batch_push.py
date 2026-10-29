#!/usr/bin/env python3
"""
High-Speed Live Job Batch Pusher
Ingests live vacancies across multi-source web feeds and pushes 50+ new jobs
in one instant batch into:
  1. outputs/application_board.json
  2. outputs/application_board.md
  3. outputs/job_applications_tracker.xlsx
  4. dossier/synced_applications.json
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import multi_source_scraper
import tracker
import excel_tracker
import dossier_sync


def batch_push_jobs(batch_size: int = 50, min_score: int = 75) -> int:
    start_time = time.time()
    print(f"\n{'='*70}")
    print(f"⚡ [Live High-Speed Ingestion] Sourcing batch of {batch_size}+ live vacancies from web...")
    print(f"{'='*70}")

    jobs = multi_source_scraper.fetch_all_multisource_jobs(target_count=batch_size + 30)
    print(f"🌐 Ingested {len(jobs)} live vacancies from Internet feeds in {time.time() - start_time:.2f}s.")

    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)
    existing_keys = {
        (a.get("company", "").strip().lower(), a.get("role", "").strip().lower())
        for a in board
    }

    pushed_count = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for j in jobs:
        if pushed_count >= batch_size:
            break

        comp = j.get("company", "").strip()
        title = j.get("title", "").strip()
        key = (comp.lower(), title.lower())

        if key in existing_keys:
            continue

        existing_keys.add(key)
        fit = j.get("fit_score", 85)

        # Build application entry with complete schema
        record = {
            "id": f"app_{len(board) + 1:04d}",
            "company": comp,
            "role": title,
            "location": j.get("location", "Remote"),
            "status": "DRAFT",
            "fit_score": fit,
            "stage_history": [
                {"stage": "DRAFT", "timestamp": now_str, "notes": f"Live Ingested from {j.get('source', 'Web')}"}
            ],
            "application_date": datetime.now().strftime("%Y-%m-%d"),
            "url": j.get("url", ""),
            "contact_email": "",
            "notes": [f"Match: {fit}%. Source: {j.get('source', 'Web')}"],
            "response_category": "Awaiting Reply",
            "last_response_snippet": "",
            "next_action": "Generate tailored outreach pitch & resume bullet points",
            "last_updated": now_str
        }

        board.append(record)
        pushed_count += 1

    # Instant batch save to JSON, Markdown, and Excel
    tracker.save_board(board, json_path, md_path)

    # Sync to Dossier
    try:
        dossier_sync.export_to_dossier()
    except Exception:
        pass

    total_time = time.time() - start_time
    print(f"\n🎉 Successfully injected {pushed_count} live jobs into Excel in {total_time:.2f} seconds!")
    print(f"📈 Total Tracked Applications in Excel: {len(board)}")
    print(f"📂 Updated Excel File: {excel_tracker.EXCEL_PATH}")
    print(f"{'='*70}\n")
    return pushed_count


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    batch_push_jobs(batch_size=count)
