#!/usr/bin/env python3
"""
Application Email & Interview Reply Drafter
Adapted from Dossier's email generation and reply engine (application-email.ts).

Generates:
  1. Cold application / founder outreach emails with pre-filled mailto: links.
  2. Interview availability and recruiter reply drafts grounded in candidate facts.
"""

import sys
import os
import json
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_candidate_profile(base_dir: Path) -> Dict[str, Any]:
    profile_path = base_dir / "inputs" / "candidate_profile.json"
    if profile_path.exists():
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_target_job(base_dir: Path, role_id: Optional[str] = None) -> Dict[str, Any]:
    # Check startup roles first, then discovered roles
    for filename in ["startup_roles.json", "discovered_roles.json"]:
        p = base_dir / "outputs" / filename
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    roles = json.load(f)
                    if role_id:
                        for r in roles:
                            if r.get("id") == role_id or role_id.lower() in r.get("company", "").lower():
                                return r
                    elif roles:
                        return roles[0]
            except Exception:
                pass
    return {
        "company": "Target Company",
        "title": "Principal AI Systems Architect",
        "direct_emails": ["hiring@example.com"],
        "snippet": "Building production AI systems, agent mesh, and low latency RAG."
    }


def make_mailto_link(to_email: str, subject: str, body: str) -> str:
    params = {
        "subject": subject,
        "body": body
    }
    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"mailto:{to_email}?{encoded_params}"


def draft_application_email(role: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, str]:
    candidate_name = profile.get("candidate_name") or "Kishor Kumar Paroi"
    headline = profile.get("headline") or "Principal AI Systems Architect"
    contact = profile.get("contact", {})
    email = contact.get("email") or "kishor.kumar.paroi.dev@gmail.com"
    linkedin = contact.get("linkedin") or "https://www.linkedin.com/in/kishorkumarparoi"
    github = contact.get("github") or "https://github.com/KishorKumarParoi"

    company = role.get("company", "the team")
    title = role.get("title", "Engineering Role")
    to_email = role.get("direct_emails", ["hiring@" + company.lower().replace(" ", "") + ".com"])[0] if role.get("direct_emails") else "hiring@" + company.lower().replace(" ", "") + ".com"

    subject = f"Application: {title} — {candidate_name}"

    try:
        import ai_inference
        custom_pitch = ai_inference.generate_custom_pitch(role, profile)
    except Exception:
        custom_pitch = (
            f"I am writing to express my strong interest in the {title} role at {company}.\n\n"
            f"As a {headline}, I design and deliver low-latency AI platforms, LangGraph agent workflows, and resilient data architectures:\n"
            "- Sub-35ms Hybrid RAG: Architected multi-stage retrieval with local ONNX re-ranking and semantic caching.\n"
            "- Scalable Agent Mesh: Built secure FastMCP and microservices supporting high concurrency and human-in-the-loop oversight.\n"
            "- High-Throughput Pipelines: Engineered medallion lakehouses and stream processing handling hundreds of thousands of events daily."
        )

    body_lines = [
        f"Hi {company} Team,",
        "",
        custom_pitch,
        "",
        f"My resume and work portfolio are attached, and you can explore my open code and systems below:",
        f"- GitHub: {github}",
        f"- LinkedIn: {linkedin}",
        "",
        "I welcome the opportunity to connect for a 15-minute conversation to explore how I can contribute.",
        "",
        "Best regards,",
        candidate_name,
        email
    ]

    body = "\n".join(body_lines)
    mailto_url = make_mailto_link(to_email, subject, body)

    return {
        "to": to_email,
        "subject": subject,
        "body": body,
        "mailto_url": mailto_url
    }


def draft_interview_reply(recruiter_name: str, available_times: List[str], profile: Dict[str, Any]) -> str:
    candidate_name = profile.get("candidate_name") or "Kishor Kumar Paroi"
    lines = [
        f"Hi {recruiter_name},",
        "",
        "Thank you for reaching out and for the invitation to connect. I would be delighted to speak with you.",
        "",
        "Here are a few times I am available for a 30-minute introductory call (all in UTC / EST):",
    ]
    for t in available_times:
        lines.append(f"- {t}")

    lines.extend([
        "",
        "If none of these windows fit your calendar, please feel free to share a link to your scheduling page or alternate times that suit you better.",
        "",
        "Looking forward to our conversation.",
        "",
        "Best regards,",
        candidate_name
    ])
    return "\n".join(lines)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    profile = load_candidate_profile(base_dir)

    target_role_id = sys.argv[1] if len(sys.argv) > 1 else None
    role = load_target_job(base_dir, target_role_id)

    print(f"📧 Drafting Outreach Email for: {role.get('company')} — {role.get('title')}")

    email_data = draft_application_email(role, profile)

    # Save to Markdown
    out_dir = base_dir / "outputs"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "application_email.md"

    md_content = f"""# Tailored Application Email

> Ready-to-send application outreach with a pre-filled `mailto:` link.

- **To**: `{email_data['to']}`
- **Subject**: `{email_data['subject']}`
- **One-Click Link**: [Click to Open in Mail Client]({email_data['mailto_url']})

---

### Email Message Body

```text
{email_data['body']}
```

---

### Recruiter Interview Reply Template

```text
{draft_interview_reply("Recruiter", ["Monday, Nov 3 at 10:00 AM EST", "Tuesday, Nov 4 at 2:00 PM EST", "Wednesday, Nov 5 at 11:00 AM EST"], profile)}
```
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Generated Application Email!")
    print(f"   To: {email_data['to']}")
    print(f"   Subject: {email_data['subject']}")
    print(f"📄 Saved to: {out_file.relative_to(base_dir)}")


if __name__ == "__main__":
    main()

def draft_offer_reply(recruiter_name: str, company: str, offer_details: Dict[str, Any], profile: Dict[str, Any], intent: str = "negotiate") -> str:
    """
    Drafts an offer response email:
      - 'accept': Formal acceptance of the job offer
      - 'negotiate': Polite counter-proposal / compensation inquiry
      - 'clarify': Asking for details on vesting, benefits, remote policy
    """
    candidate_name = profile.get("candidate_name") or "Kishor Kumar Paroi"
    role_title = offer_details.get("title", "AI Systems Engineer")

    if intent == "accept":
        return f"""Hi {recruiter_name},

Thank you very much for extending the formal offer for the {role_title} role at {company}.

I am excited about the team's mission and the impact we can make together. I am thrilled to formally accept the offer! Please let me know the next steps regarding signing the agreement, onboarding documents, and start date preparations.

Looking forward to working with everyone!

Warm regards,
{candidate_name}"""

    elif intent == "negotiate":
        return f"""Hi {recruiter_name},

Thank you so much for the offer to join {company} as {role_title}. I am really excited about the engineering challenges and the technical vision we discussed throughout the interviews.

I have reviewed the terms of the offer. Based on current market rates for Principal / Lead AI Systems roles and the depth of expertise I will be bringing in low-latency inference architectures and autonomous multi-agent pipelines, I would like to discuss whether there is flexibility on the base compensation (or equity grant / sign-on component).

Could we schedule a brief 10-minute call this week to talk through this and align on a package that works for both of us?

Thank you again for your enthusiasm and partnership during this process.

Best regards,
{candidate_name}"""

    else: # Clarify
        return f"""Hi {recruiter_name},

Thank you for sending over the formal offer for the {role_title} position at {company}!

Before finalizing the agreement, I would appreciate clarification on a few specific details:
1. Expected start date options and equipment provisioning.
2. The equity vesting schedule and acceleration terms.
3. Health, retirement, and remote-work benefits summary.

Please let me know if we can address these via email or a quick sync.

Best regards,
{candidate_name}"""
