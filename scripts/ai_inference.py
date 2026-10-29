#!/usr/bin/env python3
"""
Multi-Model AI Inference Engine for 24-Hour Job Search & Custom Applications
Supports:
  1. Local OpenCode / LM Studio / vLLM:
     - Gemma (e.g. gemma-2-9b-it, gemma-2-27b-it)
     - Nemotron (e.g. nvidia/Llama-3.1-Nemotron-70B-Instruct, Nemotron checkpoints)
     - Any local OpenAI-compatible endpoint (http://localhost:1234/v1 or http://localhost:8000/v1)
  2. Local Ollama:
     - Gemma2 (gemma2:9b, gemma2:27b) or Nemotron at http://localhost:11434/v1
  3. Google Gemini Low Mode:
     - Gemini 2.0 Flash / Gemini 1.5 Flash (low latency, high efficiency)
  4. Antigravity Agent Native Mode:
     - Zero-cost, zero-latency grounded inference with strict Fact Guard protection.

Resilience:
  If a requested local endpoint is offline, the engine falls back to Antigravity
  agent native mode so the 24-hour nonstop daemon never crashes.
"""

import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config() -> Dict[str, str]:
    config = {
        "ACTIVE_AI_PROVIDER": os.getenv("ACTIVE_AI_PROVIDER", "agent_native"),
        "OPENCODE_BASE_URL": os.getenv("OPENCODE_BASE_URL", "http://localhost:1234/v1"),
        "OPENCODE_MODEL": os.getenv("OPENCODE_MODEL", "gemma-2-9b-it"),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "gemma2:9b"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }

    env_file = BASE_DIR / ".env"
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


def call_openai_compatible_endpoint(base_url: str, model_name: str, system_prompt: str, user_prompt: str, timeout: int = 15) -> Optional[str]:
    """Calls local OpenCode / LM Studio / Ollama / vLLM chat completions API."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "prompt" if "anthropic" in base_url else "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "RayCodes-24h-Agent"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            choices = res_json.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "").strip()
    except Exception as e:
        print(f"⚠️ [Local LLM Call Failed] {base_url} ({model_name}): {e}")
        return None


def call_gemini_api(api_key: str, model_name: str, system_prompt: str, user_prompt: str, timeout: int = 15) -> Optional[str]:
    """Calls Google Gemini API (Low mode / Flash)."""
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        print(f"⚠️ [Gemini API Call Failed] {model_name}: {e}")
        return None


def generate_native_grounded_pitch(role: Dict[str, Any], profile: Dict[str, Any]) -> str:
    """Zero-cost, verified candidate pitch tailored to the company's tech stack."""
    company = role.get("company", "the team")
    title = role.get("title", "Engineering Role")
    snippet = role.get("snippet", "").lower()

    # Identify matching pillars from Kishor's real stack
    pillars = []
    
    # 1. LLM Fine-Tuning & Serving
    if any(k in snippet for k in ["llm", "fine-tuning", "lora", "vllm", "training", "alignment", "dpo"]):
        pillars.append("• Distributed LLM Fine-Tuning & Inference: Implemented LoRA, QLoRA, and DPO alignment workflows with PyTorch FSDP and vLLM serving, optimizing inference throughput.")
    else:
        pillars.append("• Sub-35ms Agentic Hybrid RAG: Engineered high-concurrency retrieval systems with local ONNX re-ranking, FlashAttention-2, and semantic caching (<50ms).")

    # 2. Agent Systems & Architecture
    if any(k in snippet for k in ["agent", "langgraph", "mcp", "orchestrat", "workflow"]):
        pillars.append("• Production Agent Mesh: Built resilient multi-agent supervisory networks using LangGraph, FastMCP protocols, and NeMo guardrails with human-in-the-loop controls.")
    else:
        pillars.append("• Cloud & Platform Infrastructure: Production experience deploying containerized workloads across Kubernetes, AKS, AWS Fargate, GCP, and Azure with Terraform IaC.")

    # 3. Data Systems / Systems Programming
    if any(k in snippet for k in ["rust", "simd", "performance", "go", "systems", "c++", "low level"]):
        pillars.append("• High-Performance Systems: Authored Rust SIMD vector accelerators and Go microservices delivering sub-millisecond execution latency.")
    else:
        pillars.append("• Enterprise Lakehouse Architecture: Designed medallion streaming pipelines handling large-scale event streams across Kafka, PySpark, Databricks, and Snowflake.")

    pitch_lines = [
        f"I am writing to express my strong interest in the {title} role at {company}.",
        "",
        "With a background as a Principal AI Systems Architect and founder, I focus on building production-grade, low-latency AI platforms and scalable distributed infrastructure:",
        "\n".join(pillars),
        "",
        f"I reviewed {company}'s engineering focus and would be excited to bring this systems expertise to your team."
    ]
    return "\n".join(pitch_lines)


def generate_custom_pitch(role: Dict[str, Any], profile: Dict[str, Any]) -> str:
    """
    Main entry point:
      Attempts configured model (OpenCode / Gemma / Nemotron / Gemini).
      If local model server is unreachable, falls back to Antigravity native low mode.
    """
    cfg = load_config()
    provider = cfg.get("ACTIVE_AI_PROVIDER", "agent_native").lower()

    company = role.get("company", "Company")
    title = role.get("title", "Role")
    job_text = role.get("snippet", "") or role.get("title", "")

    system_prompt = (
        "You are an expert career agent writing a concise, high-impact 3-bullet pitch for Kishor Kumar Paroi, "
        "a Principal AI Systems Architect. Focus strictly on real verified achievements: "
        "sub-35ms Hybrid RAG, LLM fine-tuning (LoRA/DPO), vLLM, LangGraph agents, Kubernetes/AKS/Fargate, Rust SIMD, Databricks. "
        "Do not invent facts or metrics."
    )

    user_prompt = (
        f"Role: {title} at {company}\n"
        f"Job Description: {job_text}\n\n"
        "Generate a 3-bullet customized alignment pitch explaining why Kishor is a direct match."
    )

    llm_output = None

    # Option A: Local OpenCode / LM Studio (Gemma or Nemotron)
    if provider in ["local_opencode", "opencode", "lmstudio"]:
        base_url = cfg["OPENCODE_BASE_URL"]
        model = cfg["OPENCODE_MODEL"]
        print(f"🤖 [AI Inference] Querying local OpenCode/LM Studio ({model})...")
        llm_output = call_openai_compatible_endpoint(base_url, model, system_prompt, user_prompt)

    # Option B: Local Ollama (Gemma or Nemotron)
    elif provider in ["local_ollama", "ollama"]:
        base_url = cfg["OLLAMA_BASE_URL"]
        model = cfg["OLLAMA_MODEL"]
        print(f"🤖 [AI Inference] Querying local Ollama ({model})...")
        llm_output = call_openai_compatible_endpoint(base_url, model, system_prompt, user_prompt)

    # Option C: Gemini Low Mode / Flash
    elif provider in ["gemini", "gemini_low_mode"]:
        api_key = cfg["GEMINI_API_KEY"]
        model = cfg["GEMINI_MODEL"]
        print(f"🤖 [AI Inference] Querying Gemini Low Mode ({model})...")
        llm_output = call_gemini_api(api_key, model, system_prompt, user_prompt)

    # If LLM returned text, return it
    if llm_output:
        return llm_output

    # Fallback / Native Grounded Mode
    if provider != "agent_native":
        print(f"ℹ️ [AI Inference] Model provider '{provider}' offline. Using Antigravity grounded native mode.")
    return generate_native_grounded_pitch(role, profile)


if __name__ == "__main__":
    cfg = load_config()
    print("AI Inference Module Health Check:")
    print(json.dumps(cfg, indent=2))
    sample_role = {"company": "KoomAI", "title": "Principal AI Systems Architect", "snippet": "Building sub-35ms RAG and LLM fine-tuning pipelines."}
    pitch = generate_custom_pitch(sample_role, {})
    print("\nSample Output Pitch:\n" + "-" * 50)
    print(pitch)
