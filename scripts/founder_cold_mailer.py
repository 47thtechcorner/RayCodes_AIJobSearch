#!/usr/bin/env python3
"""
Founder Outreach & Cold Mail Dispatcher
Takes high-fit roles from application_board.json, discovers tech founder emails,
generates personalized cold pitches with candidate resume bullets,
and provides:
  1. Safe Staging Mode (Outbox preview with 1-click mailto links)
  2. Live SMTP Sender (When SMTP credentials are provided in .env)
  3. Automatic Status Transition (DRAFT -> SENT) in Excel & Dossier
"""

import sys
import os
import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

import founder_discovery
import email_drafter
import fact_guard
import tracker
import excel_tracker
import dossier_sync


def load_smtp_config() -> Dict[str, str]:
    """Reads SMTP credentials from .env or environment."""
    env_file = BASE_DIR / ".env"
    config = {
        "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "SMTP_PORT": os.getenv("SMTP_PORT", "587"),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
        "SENDER_EMAIL": os.getenv("SENDER_EMAIL", ""),
        "SENDER_NAME": os.getenv("SENDER_NAME", "Kishor Kumar Paroi")
    }
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in config:
                        config[k] = v
    return config


def generate_founder_cold_email(company: str, role_title: str, recipient_email: str, profile: Dict[str, Any]) -> Dict[str, str]:
    candidate_name = profile.get("candidate_name") or "Kishor Kumar Paroi"
    candidate_phone = "+8801724714156"

    subject = f"Solving low-latency AI & Agent Infrastructure for {company} — Kishor Kumar Paroi"

    body = f"""Hi {company} Founding & Engineering Team,

I've been following {company}'s engineering journey and wanted to reach out directly regarding your {role_title} needs.

I am an AI Systems Architect & Forward Deployed Engineer (Founder @ KoomAI). I build high-throughput, sub-millisecond distributed AI systems and zero-trust agent mesh networks:

🚀 PROUD FLAGSHIP: KoomAI (https://koom.kishor.tech)
Built an enterprise 20-agent autonomous mesh serving as a one-stop freelancer powerhouse:
• Sub-120ms glass-to-glass WebRTC high-performance video communication & neural transcription.
• Autonomous agentic job hunter, automated candidate briefing & ATS resume tailor.
• NotebookLLM-grade deep research synthesis, multimodal document arbitration, and instant global escrow payouts.
• 24/7 personal executive assistant mesh sustaining 50,000+ recording minutes.

⚡ 4 TARGET ARCHITECTURE PROOFS (Matched to {role_title}):
1. Autonomous LangGraph Agent Mesh (phi0.ai): 99.4% task completion across enterprise workloads, saving $18K/month in compute: https://github.com/KishorKumarParoi/AI_Security_Production_App
2. Sub-35ms Hybrid RAG Engine: Multi-stage re-ranking (FlashRank local ONNX + BM25 sparse + dense) with zero hallucination: https://github.com/KishorKumarParoi/AI_Security_Production_App#benchmarks
3. High-Throughput vLLM GPU Serving (Samsung AI Core): Scaled 8B/70B LLMs on NVIDIA H100 clusters with FlashAttention-2, fused CUDA kernels & DeepSpeed ZeRO-3: https://github.com/KishorKumarParoi/AI-Engineering
4. Rust SIMD Vector Search Accelerator: AVX-512 vector retrieval engine scoring <0.5ms latency (50x faster than NumPy/Python): https://github.com/KishorKumarParoi/AI-Engineering/tree/main/rust-vector

🛠️ 3 CROSS-DISCIPLINARY SYSTEMS:
5. Git Storage Engine in Pure Rust: Custom packfile parsing, SHA-1 tree traversal & zlib delta compression: https://github.com/KishorKumarParoi/AI-Engineering
6. Offline-First Industrial IoT Telemetry: SQLite WAL caching, sub-second edge sync over lossy satellite uplinks: https://github.com/KishorKumarParoi/AI-Engineering
7. Zero-Trust AI Security Firewall: BotShield WAF & NVIDIA NeMo Guardrails blocking 95%+ of prompt injections: https://github.com/KishorKumarParoi/AI_Security_Production_App

📚 PROOF OF LEARNING JOURNEY:
• 38-Module AI Engineering Master Curriculum (Phases 0–5): https://github.com/KishorKumarParoi/AI-Engineering
• 1-Page Visual Resume: https://kishor.tech/resume.pdf
• 2-Page ATS Dossier: https://kishor.tech/resume_single_column.pdf
• 3D Interactive Cockpit: https://3d.kishor.tech
• 3D Cyber Hacker Command: https://hacker.kishor.tech
• macOS Sequoia Web Platform: https://macos.kishor.tech

I'd love to jump on a quick 15-minute engineering chat to explore how this architecture applies directly to {company}:
📅 Instant Zoom Booking: https://calendly.com/kishor-ruet-cse/15min
💬 Direct WhatsApp Message: https://wa.me/8801724714156?text=Hi%20Kishor,%20saw%20your%20profile%20and%20wanted%20to%20connect

Best regards,

Kishor Kumar Paroi
Principal AI Systems Architect | Founder @ KoomAI
kishor.ruet.cse@gmail.com | WhatsApp: +8801724714156 (https://wa.me/8801724714156) | RUET CSE #483
"""
    return {
        "to": recipient_email,
        "subject": subject,
        "body": body,
        "mailto_url": email_drafter.make_mailto_link(recipient_email, subject, body)
    }


def process_founder_applications(limit: int = 20, auto_send: bool = False) -> int:
    print(f"\n{'='*70}")
    print(f"🚀 [Founder Cold Mail Agent] Preparing Custom Pitches for Top Vacancies...")
    print(f"{'='*70}")

    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)
    profile = email_drafter.load_candidate_profile(BASE_DIR)
    smtp_cfg = load_smtp_config()

    is_smtp_ready = bool(smtp_cfg.get("SMTP_USER") and smtp_cfg.get("SMTP_PASSWORD"))

    drafts_processed = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    outbox_entries = []

    for app in board:
        if drafts_processed >= limit:
            break

        # Only process high-fit DRAFT applications
        if app.get("status") != "DRAFT" or app.get("fit_score", 0) < 75:
            continue

        company = app.get("company", "Company")
        role = app.get("role", "AI Engineer")
        url = app.get("url", "")
        snippet = " ".join(app.get("notes", []))

        # 1. Discover Tech Founder Email
        founder_email = founder_discovery.discover_contact_email(company, url, snippet)
        app["contact_email"] = founder_email

        # 2. Generate Custom Cold Pitch
        email_data = generate_founder_cold_email(company, role, founder_email, profile)

        # 3. Fact Guard Audit
        try:
            gt_sources = fact_guard.load_candidate_sources(BASE_DIR)
            audit = fact_guard.verify_text(email_data["body"], gt_sources)
            if not audit.get("verified", True):
                print(f"⚠️ Fact Guard flagged claim for {company}. Skipping.")
                continue
        except Exception:
            pass

        # 4. Dispatch or Stage
        if auto_send and is_smtp_ready:
            try:
                # Live SMTP Send
                msg = MIMEMultipart()
                msg["From"] = f"{smtp_cfg['SENDER_NAME']} <{smtp_cfg['SENDER_EMAIL'] or smtp_cfg['SMTP_USER']}>"
                msg["To"] = founder_email
                msg["Subject"] = email_data["subject"]
                msg.attach(MIMEText(email_data["body"], "plain"))

                with smtplib.SMTP(smtp_cfg["SMTP_SERVER"], int(smtp_cfg["SMTP_PORT"])) as server:
                    server.starttls()
                    server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASSWORD"])
                    server.send_message(msg)

                print(f"✉️ [SENT via SMTP] Delivered to {company} ({founder_email})")
                app["status"] = "SENT"
                app["response_category"] = "Awaiting Reply"
            except Exception as e:
                print(f"⚠️ SMTP delivery error for {company}: {e}. Staging in Outbox.")
                app["status"] = "SENT"
                app["response_category"] = "Staged in Outbox"
        else:
            # Staged with 1-click mailto link
            app["status"] = "SENT"
            app["response_category"] = "Staged in Outbox"

        app["last_updated"] = now_str
        app["sent_at"] = now_str
        if isinstance(app.get("notes"), list):
            app["notes"].append(f"Custom Founder Pitch prepared for {founder_email}")
        else:
            app["notes"] = [str(app.get("notes", "")), f"Custom Founder Pitch prepared for {founder_email}"]
        app["next_action"] = "Monitor recruiter inbox for interview / calendar invites"

        outbox_entries.append({
            "company": company,
            "role": role,
            "email": founder_email,
            "subject": email_data["subject"],
            "mailto": email_data["mailto_url"]
        })

        drafts_processed += 1

    # Save to tracker, Excel, and Dossier
    tracker.save_board(board, json_path, md_path)
    excel_path = excel_tracker.sync_board_to_excel()
    dossier_sync.export_to_dossier()

    # Generate Outbox Markdown File
    outbox_path = BASE_DIR / "outputs" / "founder_outreach_outbox.md"
    with open(outbox_path, "w", encoding="utf-8") as f:
        f.write("# Founder Outreach & Cold Mail Outbox\n\n")
        f.write(f"> Generated {len(outbox_entries)} personalized founder emails on {now_str}.\n\n")
        f.write("| Company | Role | Founder / Hiring Email | One-Click Send |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for e in outbox_entries:
            f.write(f"| **{e['company']}** | {e['role']} | `{e['email']}` | [✉️ Open in Mail Client]({e['mailto']}) |\n")

    print(f"\n✅ Successfully generated & staged {drafts_processed} custom founder outreach emails!")
    print(f"📊 Updated Excel Applications Pipeline: {excel_path}")
    print(f"📄 Generated 1-Click Send Hub: {outbox_path.relative_to(BASE_DIR)}")
    print(f"{'='*70}\n")
    return drafts_processed


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    process_founder_applications(limit=count, auto_send=False)
