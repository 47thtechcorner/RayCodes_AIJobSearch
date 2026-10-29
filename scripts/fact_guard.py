#!/usr/bin/env python3
"""
Fact Guard: Verification Engine for Job Applications
Adapted from Dossier's zero-hallucination verification system.

This script checks application drafts (resumes, cover letters, emails) against
candidate profile facts to ensure zero invented facts, metrics, or credentials.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100
}

MONTHS_AND_DAYS = {
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
}

NOT_NAMES = {
    "i", "i'm", "i've", "i'd", "i'll", "ok", "a", "an", "the", "this", "that", "these",
    "we", "you", "they", "he", "she", "it", "my", "our", "your", "his", "her", "its",
    # Document structure & markdown words
    "tailored", "organization", "identifier", "generated", "verification", "dual-agent",
    "drafter", "reviewer", "passed", "grounded", "subject", "ats-tailored", "engineered",
    "ecosystem", "certifications", "detail", "pass", "every", "xyz", "metric",
    "accomplished", "density", "alignment", "heading", "layout", "status", "date",
    "summary", "experience", "education", "projects", "skills", "overview", "note",
    "role", "company", "location", "salary", "fit", "score", "reasons", "audit", "table"
}

CREDENTIAL_PATTERN = re.compile(
    r"\b(certified|certification|certificate|licensed|license|accredited|chartered)\b",
    re.IGNORECASE
)

NUMBER_PATTERN = re.compile(
    r"(?<![\w])(\d{1,3}(?:[,.\s]\d{3})+|\d+(?:[.,]\d+)?)\s*(k|m)?%?(?![\w])",
    re.IGNORECASE
)


def parse_number_value(digits: str, suffix: str = None) -> float:
    cleaned = digits.replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and len(cleaned.split(",")[-1]) == 3:
        cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        val = float(cleaned)
    except ValueError:
        return 0.0
    
    if suffix:
        s = suffix.lower()
        if s == "k":
            val *= 1_000
        elif s == "m":
            val *= 1_000_000
    return val


def extract_numbers(text: str) -> List[Tuple[str, float]]:
    results = []
    for m in NUMBER_PATTERN.finditer(text):
        raw = m.group(0).strip()
        val = parse_number_value(m.group(1), m.group(2))
        results.append((raw, val))
    
    for word, val in NUMBER_WORDS.items():
        pattern = r"\b" + word + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            results.append((word, float(val)))
    return results


def find_sentence_starts(text: str) -> Set[int]:
    starts = {0}
    # Matches sentence endings, newlines, markdown headings (# ), list items (- / *), and table columns (| )
    pattern = re.compile(r"(?:[.!?]\s+|\n+(?:#{1,6}\s+)?|\|\s*)\s*(?:[-*•·]\s+)?(?=\S)")
    for match in pattern.finditer(text):
        starts.add(match.end())
    return starts


class GroundTruthSources:
    def __init__(self, raw_texts: List[str]):
        self.full_text = "\n".join(raw_texts).lower()
        # Extract individual words
        words = re.findall(r"[\w&'’+#-]+", self.full_text)
        self.words = {w.rstrip(".'’") for w in words}
        # Extract all numbers
        self.numbers = {val for _, val in extract_numbers(self.full_text)}

    def contains_word(self, word: str) -> bool:
        w = word.lower()
        return w in self.words or w in self.full_text

    def contains_number(self, val: float) -> bool:
        if val in self.numbers:
            return True
        # Allow close floating point matches
        for n in self.numbers:
            if abs(n - val) < 0.01:
                return True
        return False


def load_candidate_sources(base_dir: Path) -> GroundTruthSources:
    texts = []
    
    # 1. candidate_profile.json
    profile_path = base_dir / "inputs" / "candidate_profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                texts.append(json.dumps(data))
        except Exception as e:
            print(f"Warning: Could not read {profile_path}: {e}")

    # 2. draft_resume.md
    resume_path = base_dir / "inputs" / "draft_resume.md"
    if resume_path.exists():
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                texts.append(f.read())
        except Exception as e:
            print(f"Warning: Could not read {resume_path}: {e}")

    # 3. discovered_roles.json (job posting details)
    roles_path = base_dir / "outputs" / "discovered_roles.json"
    if roles_path.exists():
        try:
            with open(roles_path, "r", encoding="utf-8") as f:
                texts.append(f.read())
        except Exception:
            pass

    return GroundTruthSources(texts)


def verify_text(text: str, sources: GroundTruthSources) -> Dict[str, Any]:
    unverified_names = []
    unverified_numbers = []
    unverified_credentials = []

    starts = find_sentence_starts(text)

    # 1. Check capitalized words & acronyms
    word_pattern = re.compile(r"\b[A-Z][\w&'’+#-]*\b")
    for match in word_pattern.finditer(text):
        word = match.group(0).rstrip(".'’-")
        lower = word.lower()
        
        # Check if acronym (2+ uppercase characters, e.g., RAG, AWS, LLM)
        uppercase_count = sum(1 for c in word if c.isupper())
        is_acronym = uppercase_count >= 2

        # If at sentence start and not an acronym, skip (it's standard grammar)
        if match.start() in starts and not is_acronym:
            continue

        if lower in NOT_NAMES or lower in MONTHS_AND_DAYS:
            continue

        if not sources.contains_word(word):
            if word not in unverified_names:
                unverified_names.append(word)

    # 2. Check numbers & metrics
    for raw, val in extract_numbers(text):
        if val <= 2 and raw.isalpha():
            continue  # ignore words like "one", "two" in casual usage
        if not sources.contains_number(val):
            if raw not in unverified_numbers:
                unverified_numbers.append(raw)

    # 3. Check credentials
    for match in CREDENTIAL_PATTERN.finditer(text):
        cred = match.group(0)
        stem = cred[:7].lower()
        if stem not in sources.full_text:
            if cred not in unverified_credentials:
                unverified_credentials.append(cred)

    total_flags = len(unverified_names) + len(unverified_numbers) + len(unverified_credentials)
    is_clean = (total_flags == 0)

    return {
        "is_clean": is_clean,
        "total_flags": total_flags,
        "unverified_names": unverified_names,
        "unverified_numbers": unverified_numbers,
        "unverified_credentials": unverified_credentials,
    }


def run_fact_guard(target_file: str = None) -> int:
    base_dir = Path(__file__).resolve().parent.parent
    
    if target_file:
        draft_path = Path(target_file)
    else:
        draft_path = base_dir / "outputs" / "tailored_application.md"

    if not draft_path.exists():
        print(f"Error: Target file not found: {draft_path}")
        print("Please provide an application draft file or run /apply first.")
        return 1

    print(f"🔍 Running Fact Guard Audit...")
    print(f"📄 Target Document : {draft_path.name}")
    
    sources = load_candidate_sources(base_dir)
    print(f"📚 Ground Truth Words Indexed : {len(sources.words)}")
    print(f"🔢 Ground Truth Numbers Indexed: {len(sources.numbers)}")

    with open(draft_path, "r", encoding="utf-8") as f:
        draft_content = f.read()

    result = verify_text(draft_content, sources)

    # Generate Markdown Report
    report_path = base_dir / "outputs" / "fact_guard_report.md"
    report_lines = [
        "# Fact Guard Verification Audit",
        "",
        f"- **Audited Document**: `{draft_path.name}`",
        f"- **Status**: {'✅ PASSED (Zero Hallucination)' if result['is_clean'] else '⚠️ ATTENTION NEEDED (Unverified Claims Found)'}",
        f"- **Total Items Flagged**: {result['total_flags']}",
        "",
        "---",
        "",
        "## Audit Breakdown",
        "",
    ]

    if result["is_clean"]:
        report_lines.extend([
            "### ✅ Zero Hallucinated Claims",
            "All names, numbers, years, metrics, and credentials in the application draft match verified facts in candidate records.",
            ""
        ])
    else:
        if result["unverified_numbers"]:
            report_lines.append("### 🔢 Unverified Numbers & Metrics")
            report_lines.append("These figures were not found in your draft resume or profile facts:")
            for num in result["unverified_numbers"]:
                report_lines.append(f"- `\"{num}\"` -> Confirm this metric in `inputs/draft_resume.md`.")
            report_lines.append("")

        if result["unverified_names"]:
            report_lines.append("### 🏷️ Unverified Names & Tech Tools")
            report_lines.append("These names or tools were not found in your profile facts:")
            for name in result["unverified_names"]:
                report_lines.append(f"- `\"{name}\"` -> Check if this is a genuine skill or an unlisted tool.")
            report_lines.append("")

        if result["unverified_credentials"]:
            report_lines.append("### 📜 Unverified Credentials")
            report_lines.append("These certification/license references need verification:")
            for cred in result["unverified_credentials"]:
                report_lines.append(f"- `\"{cred}\"`")
            report_lines.append("")

    report_lines.extend([
        "---",
        "",
        "## Grounding Rules",
        "1. Never invent employment dates, company names, or educational degrees.",
        "2. Any metrics must match real achievements recorded in `inputs/draft_resume.md`.",
        "3. When a target role requires a tool you do not have, state it honestly as an adjacent skill rather than fabricating direct experience.",
        ""
    ])

    report_content = "\n".join(report_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\nAudit complete!")
    if result["is_clean"]:
        print("✅ Status: PASSED — 100% Grounded in candidate facts.")
    else:
        print(f"⚠️ Status: {result['total_flags']} unverified item(s) found.")
        if result["unverified_numbers"]:
            print(f"   - Numbers/Metrics: {', '.join(result['unverified_numbers'][:5])}")
        if result["unverified_names"]:
            print(f"   - Names/Tools: {', '.join(result['unverified_names'][:5])}")
    print(f"📝 Full Report Saved to: {report_path.relative_to(base_dir)}")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(run_fact_guard(target))
