#!/usr/bin/env python3
"""
Standardizes all application IDs sequentially from APP-0001 to APP-XXXX
across:
  1. outputs/application_board.json
  2. outputs/application_board.md
  3. outputs/job_applications_tracker.xlsx
  4. dossier/synced_applications.json
  5. outputs/founder_outreach.xlsx
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import tracker
import excel_tracker
import founders_crm
import continuous_batch_accumulator
import dossier_sync

def standardize_and_resync():
    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)

    print(f"Renumbering {len(board)} applications sequentially...")
    for idx, app in enumerate(board, 1):
        app["id"] = f"APP-{idx:04d}"

    # Save board
    tracker.save_board(board, json_path, md_path)
    excel_tracker.sync_board_to_excel()
    dossier_sync.export_to_dossier()

    # Re-sync Founders CRM
    crm = founders_crm.load_crm_records()
    continuous_batch_accumulator.create_or_update_founder_excel(crm)

    print(f"✅ Successfully renumbered {len(board)} applications (APP-0001 to APP-{len(board):04d})!")

if __name__ == "__main__":
    standardize_and_resync()
