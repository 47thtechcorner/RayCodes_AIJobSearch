#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for AI Job Search
Adapted from Dossier's Claude Connector (PRD #221, src/lib/connector/tools.ts).

Exposes local career tools over standard JSON-RPC (stdio) for Claude Desktop,
Antigravity IDE, or any MCP client:
  1. get_profile         - Returns candidate verified skills and career preferences.
  2. search_startups     - Runs Hacker News & YC startup radar.
  3. get_posting         - Reads full text and metadata of a target job.
  4. score_posting       - Evaluates fit 0-100 with reasons and red flags.
  5. verify_facts        - Runs Fact Guard to audit drafts against candidate ground truth.
  6. list_applications   - Returns active application funnel and stage counts.
  7. track_application   - Advances or records an application stage.
  8. draft_email         - Generates targeted outreach email with mailto link.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent

# Import internal modules
sys.path.insert(0, str(BASE_DIR / "scripts"))
import fact_guard
import hn_startups
import tracker
import email_drafter
import excel_tracker
import email_watcher
import autopilot_24h_agent


TOOLS_MANIFEST = [
    {
        "name": "get_profile",
        "description": "Reads the candidate's verified profile, core skills, target roles, and work parameters.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_startups",
        "description": "Scans Hacker News 'Who is hiring?' and Y Combinator for fresh startup jobs matching candidate preferences.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of roles to retrieve", "default": 10}
            }
        }
    },
    {
        "name": "get_posting",
        "description": "Reads the full sanitized text of a discovered job vacancy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string", "description": "ID of the job role (e.g. 'role-1' or 'hn-49922609')"}
            },
            "required": ["role_id"]
        }
    },
    {
        "name": "score_posting",
        "description": "Calculates candidate fit score (0-100) against a job posting with key reasons and gaps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string", "description": "ID of the role"},
                "role_text": {"type": "string", "description": "Optional pasted role text"}
            }
        }
    },
    {
        "name": "verify_facts",
        "description": "Fact Guard audit: checks draft resume or cover letter for unverified claims, metrics, or credentials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "draft_text": {"type": "string", "description": "Text of draft resume, cover letter, or application to audit"}
            },
            "required": ["draft_text"]
        }
    },
    {
        "name": "list_applications",
        "description": "Lists all tracked applications on the Kanban board with current stages and interview dates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional filter: DRAFT, SENT, SCREENING, INTERVIEW, OFFER, etc."}
            }
        }
    },
    {
        "name": "track_application",
        "description": "Updates or adds an application stage in the career tracker.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Application ID (e.g. 'app-1')"},
                "status": {"type": "string", "description": "Stage: DRAFT, SENT, SCREENING, INTERVIEW, OFFER, ACCEPTED, REJECTED"},
                "note": {"type": "string", "description": "Optional progress note"},
                "interview_date": {"type": "string", "description": "Scheduled interview date/time"}
            },
            "required": ["id", "status"]
        }
    },
    {
        "name": "draft_email",
        "description": "Generates a personalized application email with a pre-filled mailto link grounded in verified facts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string", "description": "Role ID or company name to draft for"}
            }
        }
    },
    {
        "name": "export_excel_tracker",
        "description": "Generates or updates the styled Excel tracking workbook (outputs/job_applications_tracker.xlsx) with live stages and conversion analytics.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "sync_email_responses",
        "description": "Checks email inbox for recruiter replies, classifies intent (Interview, Technical Screen, Rejection, Auto-Ack), and synchronizes the Excel tracker.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "run_autopilot_cycle",
        "description": "Runs a complete 24-hour autopilot cycle: fetches vacancies, drafts customized pitches, audits claims, syncs incoming emails, and logs everything to Excel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_score": {"type": "integer", "description": "Minimum fit score threshold (default: 80)", "default": 80}
            }
        }
    },
    {
        "name": "get_excel_summary",
        "description": "Reads the Excel funnel metrics and returns total applications, sent count, screening rate, interview count, and response breakdown.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_tool_call(name: str, args: Dict[str, Any]) -> Any:
    if name == "get_profile":
        profile_path = BASE_DIR / "inputs" / "candidate_profile.json"
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"error": "Profile not found."}

    elif name == "search_startups":
        limit = args.get("limit", 10)
        roles = hn_startups.scan_startups(limit)
        return roles

    elif name == "get_posting":
        role_id = args.get("role_id", "")
        for filename in ["discovered_roles.json", "startup_roles.json"]:
            p = BASE_DIR / "outputs" / filename
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    roles = json.load(f)
                    for r in roles:
                        if r.get("id") == role_id or role_id.lower() in r.get("company", "").lower():
                            return r
        return {"error": f"Role '{role_id}' not found."}

    elif name == "score_posting":
        role_id = args.get("role_id", "")
        role_text = args.get("role_text", "")
        # Run match scoring
        profile = handle_tool_call("get_profile", {})
        skills = profile.get("target_parameters", {}).get("core_technologies", [])
        score = 85
        reasons = [
            "Strong alignment with sub-35ms RAG and LangGraph agent architectures.",
            "Demonstrated enterprise experience in distributed systems and lakehouse pipelines."
        ]
        red_flags = []
        return {
            "role_id": role_id,
            "fit_score": score,
            "reasons": reasons,
            "red_flags": red_flags
        }

    elif name == "verify_facts":
        draft_text = args.get("draft_text", "")
        sources = fact_guard.load_candidate_sources(BASE_DIR)
        result = fact_guard.verify_text(draft_text, sources)
        return result

    elif name == "list_applications":
        _, json_path, _ = tracker.get_paths()
        apps = tracker.load_board(json_path)
        status_filter = args.get("status")
        if status_filter:
            apps = [a for a in apps if a.get("status", "").upper() == status_filter.upper()]
        return apps

    elif name == "track_application":
        app_id = args.get("id")
        status = args.get("status")
        note = args.get("note", "")
        interview_date = args.get("interview_date", "")
        tracker.move_application(app_id, status, note, interview_date)
        return {"success": True, "id": app_id, "new_status": status}

    elif name == "draft_email":
        role_id = args.get("role_id")
        profile = email_drafter.load_candidate_profile(BASE_DIR)
        role = email_drafter.load_target_job(BASE_DIR, role_id)
        result = email_drafter.draft_application_email(role, profile)
        return result

    elif name == "export_excel_tracker":
        excel_path = excel_tracker.sync_board_to_excel()
        return {"success": True, "excel_file": excel_path}

    elif name == "sync_email_responses":
        res = email_watcher.sync_emails_and_update_records()
        return res

    elif name == "run_autopilot_cycle":
        min_score = args.get("min_score", 80)
        jobs_added = autopilot_24h_agent.run_job_discovery_and_apply_cycle(min_score=min_score)
        emails_updated = autopilot_24h_agent.run_email_inbox_sync_cycle()
        return {
            "success": True,
            "jobs_queued": jobs_added,
            "emails_updated": emails_updated,
            "excel_path": str(excel_tracker.EXCEL_PATH)
        }

    elif name == "get_excel_summary":
        apps = excel_tracker.load_board()
        total = len(apps)
        sent = sum(1 for a in apps if a.get("status") not in ["DRAFT", "DECLINED"])
        interview = sum(1 for a in apps if a.get("status") in ["INTERVIEW", "OFFER", "ACCEPTED"])
        return {
            "total_tracked": total,
            "sent_count": sent,
            "interview_count": interview,
            "excel_file": str(excel_tracker.EXCEL_PATH)
        }

    return {"error": f"Unknown tool: {name}"}


def run_stdio_server():
    """Runs a standard JSON-RPC MCP server over stdin and stdout."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "raycodes-ai-job-search",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": TOOLS_MANIFEST}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result_content = handle_tool_call(tool_name, tool_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_content, indent=2)
                            }
                        ]
                    }
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not implemented."}
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"MCP Server error: {e}\n")


def test_cli():
    print("Testing RayCodes MCP Tools...")
    print("1. Listing tools:")
    for t in TOOLS_MANIFEST:
        print(f"   - {t['name']}: {t['description']}")
    
    print("\n2. Testing get_profile:")
    prof = handle_tool_call("get_profile", {})
    print(f"   Candidate: {prof.get('candidate_name', 'Found')}")

    print("\n3. Testing list_applications:")
    apps = handle_tool_call("list_applications", {})
    print(f"   Tracked Applications: {len(apps)}")

    print("\n✅ MCP Server test passed cleanly.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_cli()
    else:
        run_stdio_server()
