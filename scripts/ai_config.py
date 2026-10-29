#!/usr/bin/env python3
"""
Multi-Model AI Configuration & Health Check
Adapted from Dossier's AI provider architecture (src/lib/ai/provider.ts).

Detects and checks available AI backends:
  - Local: Ollama, LM Studio (Private, zero-cost, local inference)
  - Cloud: Anthropic Claude, OpenAI GPT-4o, Google Gemini, Mistral
  - Native Agent: Antigravity IDE / Claude Desktop agent runtime
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Tuple


def load_env_file(env_path: Path) -> Dict[str, str]:
    env_vars = {}
    if not env_path.exists():
        return env_vars
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("\"'")
    return env_vars


def check_url_reachability(url: str, timeout: int = 2) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RayCodes-Check"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 500
    except Exception:
        return False


def get_ai_status() -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / ".env"
    if not env_file.exists():
        env_file = base_dir / ".env.example"

    env = load_env_file(env_file)
    # Merge system env
    for k in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY"]:
        if k in os.environ and not env.get(k):
            env[k] = os.environ[k]

    ollama_url = env.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    lmstudio_url = env.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")

    # Probe endpoints
    ollama_ok = check_url_reachability(ollama_url.replace("/v1", "/api/tags"))
    lmstudio_ok = check_url_reachability(lmstudio_url.replace("/v1", "/v1/models"))

    anthropic_ok = bool(env.get("ANTHROPIC_API_KEY"))
    openai_ok = bool(env.get("OPENAI_API_KEY"))
    gemini_ok = bool(env.get("GEMINI_API_KEY"))
    mistral_ok = bool(env.get("MISTRAL_API_KEY"))

    active = env.get("ACTIVE_AI_PROVIDER", "agent_native")

    return {
        "active_selection": active,
        "providers": {
            "agent_native": {"available": True, "type": "Agent Runtime (Antigravity/Claude)", "cost": "$0.00"},
            "local_ollama": {"available": ollama_ok, "endpoint": ollama_url, "type": "Local Private LLM", "cost": "$0.00"},
            "local_lmstudio": {"available": lmstudio_ok, "endpoint": lmstudio_url, "type": "Local Private LLM", "cost": "$0.00"},
            "anthropic": {"available": anthropic_ok, "type": "Cloud API (Claude 3.5 Sonnet)", "cost": "Pay per token"},
            "openai": {"available": openai_ok, "type": "Cloud API (GPT-4o)", "cost": "Pay per token"},
            "gemini": {"available": gemini_ok, "type": "Cloud API (Gemini 2.0)", "cost": "Pay per token"},
            "mistral": {"available": mistral_ok, "type": "Cloud API (Mistral Large)", "cost": "Pay per token"}
        }
    }


def main():
    status = get_ai_status()
    print("🤖 RayCodes Multi-Provider AI Health Check:")
    print("-" * 55)
    for name, p in status["providers"].items():
        state_icon = "🟢 ACTIVE" if p["available"] else "⚪ Offline"
        print(f"  {state_icon:<12} {name:<16} | {p['type']:<30} ({p['cost']})")
    print("-" * 55)
    print(f"Current Configured Strategy: {status['active_selection']}")
    print("Note: In 'agent_native' mode, all drafting and verification run via your active chat agent.")


if __name__ == "__main__":
    main()
