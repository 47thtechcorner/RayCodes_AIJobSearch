#!/usr/bin/env python3
"""
Dossier <-> RayCodes Bridge & Exporter
Synchronizes:
  1. synced_applications.json (Job Applications Pipeline)
  2. synced_founders.json (Tech Founders & Lead Contacts Directory)
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_DIR = BASE_DIR.parent / "dossier"


def export_to_dossier():
    """Syncs applications and founders into Dossier JSON snapshots."""
    # 1. Job Applications
    raycodes_board_path = BASE_DIR / "outputs" / "application_board.json"
    if raycodes_board_path.exists():
        try:
            with open(raycodes_board_path, "r", encoding="utf-8") as f:
                board_data = json.load(f)

            dossier_apps_export = {
                "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_tracked": len(board_data),
                "applications": board_data
            }
            target_apps_path = DOSSIER_DIR / "synced_applications.json"
            with open(target_apps_path, "w", encoding="utf-8") as f:
                json.dump(dossier_apps_export, f, indent=2)
            print(f"✅ [Dossier Sync] Exported {len(board_data)} applications to dossier/synced_applications.json")
        except Exception as e:
            print(f"⚠️ Error syncing applications: {e}")

    # 2. Founders CRM Directory
    founders_crm_path = BASE_DIR / "outputs" / "founders_outreach_crm.json"
    if founders_crm_path.exists():
        try:
            with open(founders_crm_path, "r", encoding="utf-8") as f:
                founders_data = json.load(f)

            dossier_founders_export = {
                "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_founders": len(founders_data),
                "founders": founders_data
            }
            target_founders_path = DOSSIER_DIR / "synced_founders.json"
            with open(target_founders_path, "w", encoding="utf-8") as f:
                json.dump(dossier_founders_export, f, indent=2)
            print(f"✅ [Dossier Sync] Exported {len(founders_data)} founders to dossier/synced_founders.json")
        except Exception as e:
            print(f"⚠️ Error syncing founders: {e}")


if __name__ == "__main__":
    export_to_dossier()
