#!/usr/bin/env python3
"""
Gmail Label & Folder Automation Engine
Creates dedicated labels and nesting structures in candidate's Gmail via IMAP:
  1. 💼 Career-AI/Founders-Outreach
  2. 🏢 Career-AI/Company-Applications
  3. 🎯 Career-AI/Interview-Calls
  4. 🎉 Career-AI/Offers-Received
"""

import sys
import os
import imaplib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def load_credentials():
    env_file = BASE_DIR / ".env"
    creds = {"IMAP_SERVER": "imap.gmail.com", "IMAP_USER": "", "IMAP_PASSWORD": ""}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in creds:
                        creds[k] = v
    return creds

def setup_labels():
    creds = load_credentials()
    user = creds["IMAP_USER"]
    pwd = creds["IMAP_PASSWORD"]
    server_host = creds["IMAP_SERVER"]

    if not user or not pwd:
        print("⚠️ IMAP_USER or IMAP_PASSWORD not configured in .env")
        return

    print(f"Connecting to {server_host} as {user}...")
    try:
        mail = imaplib.IMAP4_SSL(server_host, 993)
        mail.login(user, pwd)
        print("✅ Authenticated with Gmail!")

        desired_folders = [
            "Career-AI",
            "Career-AI/Founders-Outreach",
            "Career-AI/Company-Applications",
            "Career-AI/Interview-Calls",
            "Career-AI/Offers-Received"
        ]

        for folder in desired_folders:
            # Gmail uses UTF-7 or simple create for ASCII folder names
            typ, res = mail.create(folder)
            if typ == "OK":
                print(f"📁 Created Gmail Label: '{folder}'")
            else:
                print(f"ℹ️ Label '{folder}' already exists or ready.")

        mail.logout()
        print("\n🎉 Dedicated Gmail Career Folders & Labels are setup successfully!")
    except Exception as e:
        print(f"❌ Error setting up Gmail labels: {e}")

if __name__ == "__main__":
    setup_labels()
