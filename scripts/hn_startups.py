#!/usr/bin/env python3
"""
Hacker News & Startup Job Radar
Adapted from Dossier's startup discovery engine (PRD #222).

Scans:
1. Hacker News monthly "Ask HN: Who is hiring?" posts via Algolia API.
2. Official Y Combinator job postings via Hacker News Firebase API.
Filters roles based on candidate profile preferences, extracts direct recruiter/founder emails,
and writes structured results to outputs/startup_roles.json and outputs/startup_radar.md.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
from html import unescape
from pathlib import Path
from typing import Dict, List, Any, Optional

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) RayCodes-JobRadar/1.0"
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=10"
HN_ITEM_URL = "https://hn.algolia.com/api/v1/items/{}"
YC_JOB_STORIES_URL = "https://hacker-news.firebaseio.com/v0/jobstories.json"
YC_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
ROLE_PATTERN = re.compile(
    r"\b(engineer|developer|architect|scientist|lead|director|head|founder|founding|sre|devops|researcher|ai|ml|data)\b",
    re.IGNORECASE
)
STAGE_PATTERN = re.compile(
    r"\b(seed|series [a-e]|pre-seed|bootstrapped|profitable|yc [wsfpx]\d{2})\b",
    re.IGNORECASE
)


def fetch_json(url: str, timeout: int = 10) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            return json.loads(data)
    except Exception as e:
        # Graceful fallback on network timeout
        return None


def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = unescape(raw_html)
    # Replace breaks and paragraphs with newlines
    text = re.sub(r"<p\s*/?>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Normalize excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_hn_whoishiring_post(comment: Dict[str, Any], preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    text = clean_html(comment.get("text", ""))
    if not text or len(text) < 40:
        return None

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    header = lines[0]
    parts = [p.strip() for p in re.split(r"\s*\|\s*", header) if p.strip()]
    if not parts:
        return None

    company = re.sub(r"https?://\S+", "", parts[0])
    company = re.sub(r"\s*\(.*\)\s*$", "", company).strip()
    if len(company) < 2 or len(company) > 100:
        return None

    header_lower = header.lower()
    is_remote = "remote" in header_lower or "anywhere" in header_lower or "distributed" in header_lower
    
    # Check location alignment
    user_location = preferences.get("location", "Remote").lower()
    allow_any_remote = preferences.get("allow_remote", True)

    if not is_remote and allow_any_remote and user_location in ["remote", "worldwide"]:
        # Skip purely on-site roles in other regions if candidate prefers remote
        if any(city in header_lower for city in ["sf only", "nyc only", "on-site only", "in-office only"]):
            return None

    # Extract emails
    emails = list(set(EMAIL_PATTERN.findall(text)))
    
    # Extract links
    urls = list(set(URL_PATTERN.findall(text)))
    website = ""
    for u in urls:
        if "news.ycombinator.com" not in u and "algolia.com" not in u:
            website = u
            break

    # Extract stage
    stage_match = STAGE_PATTERN.search(header)
    stage = stage_match.group(0).upper() if stage_match else "Startup"

    # Extract roles mentioned
    roles = [p for p in parts if ROLE_PATTERN.search(p) and len(p) < 120]
    title = roles[0] if roles else parts[1] if len(parts) > 1 else "Engineering / AI Role"

    item_id = comment.get("id") or comment.get("objectID")
    post_link = f"https://news.ycombinator.com/item?id={item_id}" if item_id else ""

    return {
        "id": f"hn-{item_id}",
        "source": "Hacker News (Who is hiring?)",
        "company": company,
        "title": title,
        "stage": stage,
        "location": " · ".join(parts[1:3]) if len(parts) > 2 else ("Remote" if is_remote else "Hybrid / On-site"),
        "remote": is_remote,
        "direct_emails": emails,
        "website": website,
        "application_url": post_link,
        "snippet": lines[1] if len(lines) > 1 else header,
        "full_text": text[:4000],
    }


def parse_yc_job(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if item.get("type") != "job" or item.get("dead") or item.get("deleted"):
        return None

    title_raw = item.get("title", "")
    if not title_raw:
        return None

    # Format: "Acme (YC W24) Is Hiring a Founding Engineer in SF"
    batch = ""
    batch_match = re.search(r"\(\s*YC\s+([A-Z]\d{2})\s*\)", title_raw, re.IGNORECASE)
    if batch_match:
        batch = f"YC {batch_match.group(1).upper()}"

    company_part = re.sub(r"\(\s*YC\s+[A-Z]\d{2}\s*\)", "", title_raw)
    company_match = re.split(r"\s+(?:is|are)\s+hiring\b", company_part, flags=re.IGNORECASE)
    company = company_match[0].strip() if company_match else title_raw[:40]

    role_part = company_match[1].strip() if len(company_match) > 1 else "Founding Engineer"
    role_part = re.sub(r"^(?:an?|for|a)\s+", "", role_part, flags=re.IGNORECASE).strip()

    is_remote = "remote" in title_raw.lower()
    url = item.get("url", "")
    item_id = item.get("id")
    hn_link = f"https://news.ycombinator.com/item?id={item_id}" if item_id else ""

    text = clean_html(item.get("text", ""))

    return {
        "id": f"yc-{item_id}",
        "source": "Y Combinator (Hacker News Jobs)",
        "company": company,
        "title": role_part or "Founding Engineer",
        "stage": batch or "YC Startup",
        "location": "Remote" if is_remote else "San Francisco / Hybrid",
        "remote": is_remote,
        "direct_emails": list(set(EMAIL_PATTERN.findall(text))),
        "website": url or hn_link,
        "application_url": url or hn_link,
        "snippet": title_raw,
        "full_text": text[:4000] if text else title_raw,
    }


def score_startup_fit(role: Dict[str, Any], target_keywords: List[str]) -> int:
    score = 60  # Base fit for vetted startup openings
    text = (role["title"] + " " + role["snippet"] + " " + role["full_text"]).lower()

    if role.get("remote"):
        score += 15

    if role.get("direct_emails"):
        score += 10  # High value: direct recruiter/founder contact

    matches = 0
    for kw in target_keywords:
        if kw.lower() in text:
            matches += 1
            score += 5

    return min(score, 100)


def scan_startups(max_results: int = 15) -> List[Dict[str, Any]]:
    base_dir = Path(__file__).resolve().parent.parent
    profile_path = base_dir / "inputs" / "candidate_profile.json"
    
    preferences = {"location": "Remote", "allow_remote": True}
    target_keywords = ["AI", "LLM", "Architect", "Python", "Rust", "Platform", "Engineer", "Distributed", "MLOps"]

    if profile_path.exists():
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "target_parameters" in data:
                    tp = data["target_parameters"]
                    preferences["location"] = tp.get("preferred_location", "Remote")
                    target_keywords.extend(tp.get("target_roles", []))
                    target_keywords.extend(tp.get("core_technologies", []))
        except Exception:
            pass

    found_roles: List[Dict[str, Any]] = []

    # 1. Query Hacker News "Who is hiring?"
    print("🌐 Fetching latest 'Ask HN: Who is hiring?' thread...")
    hn_search = fetch_json(HN_SEARCH_URL)
    if hn_search and "hits" in hn_search and len(hn_search["hits"]) > 0:
        hiring_thread = None
        for hit in hn_search["hits"]:
            title = hit.get("title", "")
            if re.match(r"^ask hn: who is hiring\?", title, re.IGNORECASE):
                hiring_thread = hit
                break
        
        if hiring_thread:
            thread_id = hiring_thread.get("objectID")
            print(f"📖 Ingesting thread: '{hiring_thread.get('title')}' (ID: {thread_id})...")
            thread_data = fetch_json(HN_ITEM_URL.format(thread_id))
            if thread_data and "children" in thread_data:
                for comment in thread_data["children"][:80]:
                    parsed = parse_hn_whoishiring_post(comment, preferences)
                    if parsed:
                        found_roles.append(parsed)

    # 2. Query YC Jobs
    print("🚀 Fetching active Y Combinator job postings...")
    yc_ids = fetch_json(YC_JOB_STORIES_URL)
    if yc_ids and isinstance(yc_ids, list):
        for jid in yc_ids[:25]:
            item = fetch_json(YC_ITEM_URL.format(jid))
            if item:
                parsed = parse_yc_job(item)
                if parsed:
                    found_roles.append(parsed)

    # Score and rank
    for role in found_roles:
        role["fit_score"] = score_startup_fit(role, target_keywords)

    found_roles.sort(key=lambda r: r["fit_score"], reverse=True)
    selected = found_roles[:max_results]

    # Save outputs
    out_dir = base_dir / "outputs"
    out_dir.mkdir(exist_ok=True)

    json_path = out_dir / "startup_roles.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2)

    # Generate Markdown Radar
    md_path = out_dir / "startup_radar.md"
    md_lines = [
        "# Startup & Hacker News Job Radar",
        "",
        f"> Live startup opportunities with direct founder and hiring team contacts.",
        "",
        "| Score | Company | Role | Stage | Location | Direct Email / Link |",
        "|:---:|:---|:---|:---|:---|:---|",
    ]

    for r in selected:
        emails_str = ", ".join(f"[{e}](mailto:{e})" for e in r["direct_emails"]) if r["direct_emails"] else f"[Apply Post]({r['application_url']})"
        score_badge = f"**{r['fit_score']}%**"
        md_lines.append(f"| {score_badge} | **{r['company']}** | {r['title']} | `{r['stage']}` | {r['location']} | {emails_str} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## Detailed Postings & Context",
        ""
    ])

    for idx, r in enumerate(selected, 1):
        md_lines.extend([
            f"### {idx}. {r['company']} — {r['title']} ({r['stage']})",
            f"- **Fit Rating**: `{r['fit_score']}/100`",
            f"- **Location**: {r['location']} ({'Remote Friendly' if r['remote'] else 'On-site/Hybrid'})",
            f"- **Posting Source**: {r['source']}",
            f"- **Direct Emails**: {', '.join(r['direct_emails']) if r['direct_emails'] else 'None listed (use application URL)'}",
            f"- **Application URL**: {r['application_url']}",
            f"- **Summary**: {r['snippet']}",
            "",
            "```text",
            r['full_text'][:1200] + ("..." if len(r['full_text']) > 1200 else ""),
            "```",
            "",
            "---",
            ""
        ])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n✅ Discovered {len(selected)} high-alignment startup roles!")
    print(f"📁 JSON Saved to: {json_path.relative_to(base_dir)}")
    print(f"📄 Markdown Radar Saved to: {md_path.relative_to(base_dir)}")
    return selected


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 15
    scan_startups(count)
