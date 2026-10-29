#!/usr/bin/env python3
"""
Strict 100% Remote Filter & Purge Engine
Applies strict remote validation across all pipeline stores:
  1. Keeps ONLY roles explicitly marked as Remote / Worldwide / Anywhere / Distributed / WFH.
  2. Updates and filters:
     - outputs/application_board.json
     - outputs/application_board.md
     - outputs/job_applications_tracker.xlsx
     - outputs/founders_outreach_crm.json
     - outputs/founder_outreach.xlsx
     - dossier/synced_applications.json
     - dossier/synced_founders.json
"""

import sys
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import tracker
import excel_tracker
import founders_crm
import continuous_batch_accumulator
import dossier_sync

REMOTE_TERMS = [
    "remote", "worldwide", "anywhere", "global", "work from home", "wfh",
    "distributed", "telecommute", "virtual", "remote-first", "100% remote",
    "remote worldwide", "remote in usa", "remote us", "remote (us)"
]


def is_strictly_remote(location_str: str, title: str = "", snippet: str = "") -> bool:
    blob = f"{location_str} {title} {snippet}".lower()
    # Check for remote markers
    if any(term in blob for term in REMOTE_TERMS):
        # Exclude strictly on-site phrases unless marked as remote option
        if "on-site only" in blob or "no remote" in blob or "hybrid only" in blob:
            return False
        return True
    return False


def purge_and_keep_remote_only():
    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)

    initial_jobs = len(board)
    remote_board = []

    for a in board:
        loc = a.get("location", "")
        role = a.get("role", "")
        notes = " ".join(a.get("notes", [])) if isinstance(a.get("notes"), list) else str(a.get("notes", ""))

        if is_strictly_remote(loc, role, notes):
            remote_board.append(a)

    print(f"🧹 Filtered Job Board: {initial_jobs} total -> {len(remote_board)} STRICTLY REMOTE jobs.")

    # Renumber sequentially
    for idx, a in enumerate(remote_board, 1):
        a["id"] = f"APP-{idx:04d}"

    # Filter CRM to match only companies that have remote roles
    remote_companies = {normalize_str(a["company"]) for a in remote_board}

    crm_records = founders_crm.load_crm_records()
    initial_crm = len(crm_records)
    remote_crm = []

    for c in crm_records:
        comp_norm = normalize_str(c.get("company", ""))
        role = c.get("role", "")
        notes = c.get("notes", "")

        if comp_norm in remote_companies or is_strictly_remote("", role, notes):
            remote_crm.append(c)

    print(f"🧹 Filtered Founders CRM: {initial_crm} total -> {len(remote_crm)} REMOTE-FRIENDLY founders.")

    for idx, c in enumerate(remote_crm, 1):
        c["crm_id"] = f"FND-{idx:04d}"

    # Save filtered Job Board & Excel
    tracker.save_board(remote_board, json_path, md_path)
    excel_tracker.sync_board_to_excel()

    # Save filtered CRM & Excel
    founders_crm.save_crm_records(remote_crm)
    founders_crm.sync_crm_to_excel(remote_crm)
    continuous_batch_accumulator.create_or_update_founder_excel(remote_crm)

    # Sync to Dossier
    dossier_sync.export_to_dossier()

    print("\n✅ Strict Remote-Only Purge Complete!")
    print(f"📈 Strictly Remote Applications: {len(remote_board)} in job_applications_tracker.xlsx")
    print(f"📈 Strictly Remote Founders: {len(remote_crm)} in founder_outreach.xlsx")


def normalize_str(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", s).lower()


if __name__ == "__main__":
    purge_and_keep_remote_only()
