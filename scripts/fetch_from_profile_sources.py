#!/usr/bin/env python3
"""
Deep Profile-Driven Job Ingestion Engine
Reads:
  - dossier/candidate_profile.json
Extracts candidate target roles:
  - Principal AI Systems Architect, LLM/RAG Engineer, Agentic AI, MLOps, Data Engineer, etc.
Extracts target job sources:
  - RemoteOK, Remotive, We Work Remotely (WWR), Hacker News, Y Combinator, Jobicy, GitHub Jobs, Ashby/Greenhouse feeds
Filters against candidate profile keywords and injects matched roles directly into:
  - outputs/application_board.json
  - outputs/job_applications_tracker.xlsx
  - dossier/synced_applications.json
"""

import sys
import os
import re
import json
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from html import unescape
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_DIR = BASE_DIR.parent / "dossier"
PROFILE_PATH = DOSSIER_DIR / "candidate_profile.json"

sys.path.insert(0, str(BASE_DIR / "scripts"))
import tracker
import excel_tracker
import dossier_sync

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def load_candidate_criteria() -> Tuple[Set[str], List[str], int]:
    """Loads target roles and keywords from dossier/candidate_profile.json."""
    if not PROFILE_PATH.exists():
        print(f"⚠️ Profile file not found at {PROFILE_PATH}")
        return set(), [], 70

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = data.get("candidate_profile", {})
    search_params = data.get("search_parameters", {})

    target_roles = profile.get("target_roles", [])
    min_score = search_params.get("min_fit_score", 70)

    # Keywords for fast token matching
    keywords = {
        "ai", "ml", "machine learning", "deep learning", "llm", "rag", "agents",
        "agentic", "systems", "architect", "nlp", "computer vision", "vllm", "lora",
        "dpo", "langgraph", "langchain", "data engineer", "lakehouse", "databricks",
        "spark", "pyspark", "kafka", "dbt", "mlops", "llmops", "platform",
        "forward deployed", "solutions architect", "rust", "python", "kubernetes"
    }
    return keywords, target_roles, min_score


def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    return " ".join(unescape(clean).split())


def calculate_profile_alignment_score(title: str, text: str, target_roles: List[str], keywords: Set[str]) -> Tuple[int, List[str]]:
    combined = f"{title} {text}".lower()
    score = 65
    matched_highlights = []

    # Direct role match
    title_lower = title.lower()
    for role in target_roles:
        if role.lower() in title_lower:
            score += 20
            matched_highlights.append(f"Direct Role Match: {role}")
            break

    # Keyword match scoring
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", combined):
            score += 3
            if len(matched_highlights) < 4:
                matched_highlights.append(kw.upper())

    score = min(99, score)
    return score, matched_highlights


# --- Source 1: Remotive API (Remote Tech & AI) ---
def fetch_remotive_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=60"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("jobs", [])[:limit]:
                title = item.get("title", "")
                company = item.get("company_name", "")
                desc = clean_html(item.get("description", ""))
                jobs.append({
                    "source": "Remotive",
                    "company": company.strip(),
                    "title": title.strip(),
                    "url": item.get("url", ""),
                    "location": item.get("candidate_required_location", "Remote Worldwide"),
                    "snippet": desc[:300]
                })
    except Exception as e:
        print(f"⚠️ Remotive fetch note: {e}")
    return jobs


# --- Source 2: We Work Remotely RSS Feed ---
def fetch_wwr_jobs(limit: int = 40) -> List[Dict[str, Any]]:
    url = "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_text = resp.read().decode("utf-8")
            root = ET.fromstring(xml_text)
            for item in root.findall("./channel/item")[:limit]:
                title_full = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = clean_html(item.findtext("description", ""))

                # WWR format: "Company Name: Job Title"
                if ":" in title_full:
                    company, title = title_full.split(":", 1)
                else:
                    company, title = "WWR Tech", title_full

                jobs.append({
                    "source": "We Work Remotely",
                    "company": company.strip(),
                    "title": title.strip(),
                    "url": link.strip(),
                    "location": "Worldwide / Remote",
                    "snippet": desc[:300]
                })
    except Exception as e:
        print(f"⚠️ WWR RSS fetch note: {e}")
    return jobs


# --- Source 3: RemoteOK API ---
def fetch_remoteok_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    url = "https://remoteok.com/api"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data[1:limit+1]:
                if not isinstance(item, dict):
                    continue
                jobs.append({
                    "source": "RemoteOK",
                    "company": item.get("company", "").strip(),
                    "title": item.get("position", "").strip(),
                    "url": item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id', '')}",
                    "location": item.get("location", "Remote"),
                    "snippet": clean_html(item.get("description", ""))[:300]
                })
    except Exception as e:
        print(f"⚠️ RemoteOK fetch note: {e}")
    return jobs


# --- Source 4: Hacker News Who is Hiring Stream ---
def fetch_hn_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    url = "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_whoishiring&hitsPerPage=70"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("hits", [])[:limit]:
                text = clean_html(item.get("comment_text", ""))
                if len(text) < 50:
                    continue
                first_line = text.split("\n")[0]
                parts = [p.strip() for p in re.split(r"[|•-]", first_line) if p.strip()]
                company = parts[0] if parts else "HN Startup"
                title = parts[1] if len(parts) > 1 else "AI Systems / Software Engineer"

                jobs.append({
                    "source": "HackerNews (Who is Hiring)",
                    "company": company[:40],
                    "title": title[:60],
                    "url": f"https://news.ycombinator.com/item?id={item.get('objectID', '')}",
                    "location": "Remote / Hybrid",
                    "snippet": text[:300]
                })
    except Exception as e:
        print(f"⚠️ Hacker News fetch note: {e}")
    return jobs



# --- Source 6: Simplify Global Engineering & AI Direct ATS Feed ---

# Global rotating offset so every 5-minute cycle injects a fresh set of 50-100 roles
OFFSET_FILE = BASE_DIR / "outputs" / ".simplify_offset.txt"

def get_and_increment_offset(batch_size: int = 150) -> int:
    offset = 0
    if OFFSET_FILE.exists():
        try:
            with open(OFFSET_FILE, "r") as f:
                offset = int(f.read().strip())
        except Exception:
            offset = 0
    new_offset = offset + batch_size
    try:
        with open(OFFSET_FILE, "w") as f:
            f.write(str(new_offset))
    except Exception:
        pass
    return offset

def fetch_simplify_jobs(limit: int = 150) -> List[Dict[str, Any]]:
    url = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            offset = get_and_increment_offset(limit)
            for item in data[offset:]:
                if not item.get("active", True):
                    continue
                title = item.get("title", "")
                company = item.get("company_name", "")
                locations = item.get("locations", [])
                loc_str = ", ".join(locations) if locations else "Remote / Global"
                
                # Check for tech/engineering relevance
                t_low = title.lower()
                if not any(k in t_low for k in ["ai", "ml", "engineer", "data", "software", "systems", "architect", "platform", "model", "llm", "cloud", "full stack", "backend"]):
                    continue

                jobs.append({
                    "source": "Simplify / Direct ATS",
                    "company": company.strip(),
                    "title": title.strip(),
                    "url": item.get("url", ""),
                    "location": loc_str,
                    "snippet": f"{title} at {company}. Category: {item.get('category', 'Tech')}. Sponsorship: {item.get('sponsorship', 'Available')}"
                })
                if len(jobs) >= limit:
                    break
    except Exception as e:
        print(f"⚠️ Simplify fetch note: {e}")
    return jobs

# --- Source 5: Jobicy Remote AI API ---
def fetch_jobicy_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    url = "https://jobicy.com/api/v2/remote-jobs?count=50"
    jobs = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("jobs", [])[:limit]:
                jobs.append({
                    "source": "Jobicy",
                    "company": item.get("companyName", "").strip(),
                    "title": item.get("jobTitle", "").strip(),
                    "url": item.get("url", ""),
                    "location": item.get("jobGeo", "Remote"),
                    "snippet": clean_html(item.get("jobExcerpt", "") or item.get("jobDescription", ""))[:300]
                })
    except Exception as e:
        print(f"⚠️ Jobicy fetch note: {e}")
    return jobs


def run_profile_matched_fetch(batch_size: int = 60) -> int:
    start_time = time.time()
    print("=" * 70)
    print("🎯 [Candidate Profile Matcher] Ingesting jobs matching desired target roles...")
    print("=" * 70)

    keywords, target_roles, min_score = load_candidate_criteria()
    print(f"📋 Loaded {len(target_roles)} target roles & {len(keywords)} technical keywords from candidate_profile.json.")
    print(f"⚖️ Minimum Fit Score Filter: {min_score}%")

    # Collect from all active verified sources
    raw_candidates = []
    print("\n🌐 Querying live feeds (Remotive, We Work Remotely, RemoteOK, Hacker News, Jobicy)...")
    raw_candidates.extend(fetch_remotive_jobs(limit=40))
    raw_candidates.extend(fetch_wwr_jobs(limit=30))
    raw_candidates.extend(fetch_remoteok_jobs(limit=40))
    raw_candidates.extend(fetch_hn_jobs(limit=40))
    raw_candidates.extend(fetch_jobicy_jobs(limit=40))
    raw_candidates.extend(fetch_simplify_jobs(limit=150))
    print(f"📥 Pulled {len(raw_candidates)} total vacancies across verified endpoints.")

    # Load existing applications
    _, json_path, md_path = tracker.get_paths()
    board = tracker.load_board(json_path)
    existing_keys = {
        (a.get("company", "").strip().lower(), a.get("role", "").strip().lower())
        for a in board
    }

    matched_jobs = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for raw in raw_candidates:
        company = raw.get("company", "").strip()
        title = raw.get("title", "").strip()
        key = (company.lower(), title.lower())

        if not company or not title or key in existing_keys:
            continue

        score, highlights = calculate_profile_alignment_score(
            title=title,
            text=raw.get("snippet", ""),
            target_roles=target_roles,
            keywords=keywords
        )

        if score >= min_score:
            existing_keys.add(key)
            matched_jobs.append({
                "id": f"app_{len(board) + len(matched_jobs) + 1:04d}",
                "company": company,
                "role": title,
                "location": raw.get("location", "Remote"),
                "status": "DRAFT",
                "fit_score": score,
                "stage_history": [
                    {"stage": "DRAFT", "timestamp": now_str, "notes": f"Matched Profile from {raw.get('source')}"}
                ],
                "application_date": datetime.now().strftime("%Y-%m-%d"),
                "url": raw.get("url", ""),
                "contact_email": "",
                "notes": [f"Fit: {score}%. Matched: {', '.join(highlights[:3])}. Source: {raw.get('source')}"],
                "response_category": "Awaiting Reply",
                "last_response_snippet": "",
                "next_action": "Generate tailored outreach pitch & resume bullet points",
                "last_updated": now_str
            })

    # Sort descending by fit score
    matched_jobs.sort(key=lambda x: x["fit_score"], reverse=True)
    selected_to_push = matched_jobs[:batch_size]

    if not selected_to_push:
        print("ℹ️ No new unseen jobs matching the criteria in this cycle.")
        return 0

    # Add to board and save
    board.extend(selected_to_push)
    tracker.save_board(board, json_path, md_path)

    # Sync to Dossier
    try:
        dossier_sync.export_to_dossier()
    except Exception:
        pass

    total_time = time.time() - start_time
    print(f"\n🎉 Successfully matched & injected {len(selected_to_push)} high-fit jobs in {total_time:.2f}s!")
    print(f"📈 Total Tracked Applications in Excel: {len(board)}")
    print(f"📂 Updated Excel File: {excel_tracker.EXCEL_PATH}")
    print("=" * 70)
    return len(selected_to_push)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    run_profile_matched_fetch(batch_size=count)
