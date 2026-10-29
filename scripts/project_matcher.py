#!/usr/bin/env python3
"""
Hyper-Irresistible Recruiter & Founder Outreach Engine with 15 Verified Projects
Architected for:
  - 3-5 Second Attention Span Shortlisting
  - Radical Risk Inversion: "2-Week Free Production Trial on your toughest bottleneck" + "Immediate Assessment Test"
  - 'Jack of All Trades, Master of Many' positioning (Compiler/SIMD -> AI RAG -> Lakehouse -> 3D WebGL)
  - 1-Click WhatsApp Direct Chat & Calendly 15-Minute Zoom Booking Integration
  - Dual Plain Text + Responsive HTML Email Formatting
  - Deep Dynamic Project Mapping across all 15 Production Projects from Master Resume & GitHub README
"""

import sys
import re
import urllib.parse
from typing import Dict, List, Any, Tuple

# All 15 Verified Flagship Projects from Master Resume & GitHub README
ALL_15_PROJECTS = {
    "1_ZOMATO_LAKEHOUSE": {
        "id": 1,
        "title": "Zomato AI Lakehouse & Multimodal Dispute Platform",
        "url": "https://github.com/KishorKumarParoi/zomato-analysis",
        "stack": "Snowflake • PySpark Delta Lake • dbt SCD-2 • Feast Feature Store • Computer Vision Anti-Fraud",
        "metric": "Ingested 35M+ orders (2.3 GB); slashed warehouse compute by 42% ($18K/mo); neutralized refund dispute fraud by 68% ($1.2M saved).",
        "tags": ["lakehouse", "spark", "pyspark", "snowflake", "delta lake", "dbt", "data", "etl", "feast", "computer vision", "redis", "kafka", "debezium"]
    },
    "2_HYBRID_ANIME_LLMOPS": {
        "id": 2,
        "title": "Hybrid Anime Intelligence & Continuous LLMOps Platform",
        "url": "https://github.com/KishorKumarParoi/Hybrid-Anime-Recommender",
        "stack": "Polyglot Mesh (Rust SIMD / Go 1.24 / FastAPI) • Dynamic Multi-LoRA vLLM • RSLoRA Flywheel",
        "metric": "Sub-0.5ms vector scoring via Rust SIMD (50x speedup over Python); 68% GPU cost reduction with vLLM Multi-LoRA continuous batching; NDCG@10 = 0.94.",
        "tags": ["rust", "simd", "vllm", "lora", "fine-tuning", "llmops", "go", "fastapi", "kafka", "inference", "gpu", "recommendation"]
    },
    "3_ENTERPRISE_AI_SECURITY": {
        "id": 3,
        "title": "Enterprise AI Security & Production Agentic RAG Platform",
        "url": "https://github.com/KishorKumarParoi/AI_Security_Production_App",
        "stack": "Zero-Trust AI Gateway • NVIDIA NeMo Guardrails • LangGraph • FastMCP • BotShield WAF",
        "metric": "Sub-35ms Hybrid RAG (Qdrant + BM25 + FlashRank ONNX); blocked 95%+ prompt injections (Microsoft PyRIT); saved $8.4K/mo (42%) via semantic similarity caching.",
        "tags": ["rag", "agent", "langgraph", "security", "guardrails", "nemo", "fastmcp", "hitl", "llm", "genai", "waf", "qdrant", "onnx"]
    },
    "4_SMART_MANUFACTURING": {
        "id": 4,
        "title": "Smart Manufacturing Industrial AI & Multi-Cloud MLOps",
        "url": "https://github.com/KishorKumarParoi/smart-manufacturing",
        "stack": "Rust Edge SIMD • PyTorch Autoencoders • GKE / K3s CNCF • ArgoCD GitOps • TensorRT INT8",
        "metric": "Sub-20ms PyTorch CNN defect classification; reduced defect escape by 31% ($420K annual scrap savings); automated 12-stage ArgoCD GitOps CI/CD.",
        "tags": ["manufacturing", "edge", "rust", "simd", "pytorch", "argocd", "gitops", "k8s", "kubernetes", "gke", "tensorrt", "mlops"]
    },
    "5_NEXUS_AI_LAKEHOUSE": {
        "id": 5,
        "title": "Nexus-AI: Enterprise Multi-Cloud Lakehouse & Autonomous Agent Mesh",
        "url": "https://github.com/KishorKumarParoi/Nexus_AI",
        "stack": "Medallion Lakehouse (Bronze-Silver-Gold) • 5-Agent LangGraph Mesh • DuckDB • Terraform",
        "metric": "5-agent LangGraph mesh accelerated analytics turnaround by 82%; DuckDB compressed dashboard query latencies from 4.5s to <120ms across AWS, GCP, and Azure.",
        "tags": ["lakehouse", "duckdb", "langgraph", "agent", "agents", "terraform", "aws", "gcp", "azure", "multi-cloud", "nl2sql"]
    },
    "6_ADVANCED_AI_CHATBOT": {
        "id": 6,
        "title": "Advanced AI Chatbot: Enterprise Autonomous Agent & HITL Platform",
        "url": "https://github.com/KishorKumarParoi/Advanced_AI_Chatbot_Project",
        "stack": "LangGraph Cyclic State Machine • FastMCP • HITL Financial Gating • BotShield WAF",
        "metric": "Multi-turn thread persistence with dynamic rollbacks; FastMCP approval gates on transactions >$50; <12ms semantic caching saving $3.2K/mo.",
        "tags": ["chatbot", "conversational", "langgraph", "fastmcp", "hitl", "agent", "agents", "waf", "qdrant", "redis"]
    },
    "7_DATA_AGENT_BI": {
        "id": 7,
        "title": "Data Agent: Multi-Agent Business Intelligence & Self-Healing SQL",
        "url": "https://github.com/KishorKumarParoi/Data-Agent",
        "stack": "Hierarchical LangGraph Mesh • Self-Healing SQL LLM Judge • ReAct ETL Sandbox",
        "metric": "96.2% query routing accuracy; LLM security judge auto-heals 89% of initial SQL errors and intercepts 100% of injection attacks; cuts pipeline cycles by 75%.",
        "tags": ["data agent", "sql", "nl2sql", "langgraph", "bi", "etl", "react", "pandas", "analytics", "agent"]
    },
    "8_NETWORK_SECURITY_ETL": {
        "id": 8,
        "title": "Advanced Network Security Medallion Lakehouse & Distributed ML",
        "url": "https://github.com/KishorKumarParoi/Advanced_ETL_Project",
        "stack": "Azure Data Factory (ADF v2) • ADLS Gen2 • Databricks Spark • Synapse CETAS • Sub-4ms ML",
        "metric": "Processes 1.4B security logs with dynamic partition pruning and Z-Order clustering; containerized ONNX inference reduced p99 latency by 11.8x.",
        "tags": ["azure", "databricks", "spark", "adls", "synapse", "etl", "lakehouse", "security", "distributed", "onnx"]
    },
    "9_AWS_SAGEMAKER_MLOPS": {
        "id": 9,
        "title": "AWS SageMaker End-to-End MLOps Pipeline & Governance Platform",
        "url": "https://github.com/KishorKumarParoi/Aws-Sagemaker",
        "stack": "SageMaker Pipelines (DAG) • Managed Spot Training • Model Registry • DataCaptureConfig",
        "metric": "Automated SageMaker DAG with Managed Spot training slashing costs by 70%; autoscaling serverless endpoints sustaining 2,500 req/s with automated drift alerts.",
        "tags": ["sagemaker", "aws", "mlops", "pipeline", "spot", "model registry", "drift", "governance", "kms"]
    },
    "10_REALTIME_MLOPS_KSERVE": {
        "id": 10,
        "title": "Cloud-Native Real-Time MLOps: KServe, AWS ECS Fargate & Kubernetes",
        "url": "https://github.com/KishorKumarParoi/realtime-mlops",
        "stack": "KServe v1beta1 • AWS ECS Fargate • Kubernetes • Modular Terraform IaC • Trivy CVE",
        "metric": "Scale-to-zero serverless inference cutting idle compute spend by 65%; 90/10 canary traffic routing with automated Prometheus latency rollbacks (>25ms).",
        "tags": ["kserve", "kubernetes", "k8s", "ecs", "fargate", "terraform", "mlops", "serving", "serverless", "devops"]
    },
    "11_RUST_GIT_ENGINE": {
        "id": 11,
        "title": "Core Systems Engineering: Rust Git Engine & POSIX Terminal Shell",
        "url": "https://github.com/KishorKumarParoi/codecrafters-git-rust",
        "stack": "Rust 1.85 Bare-Metal • SHA-1 DAG Graph • SIMD Zlib Decompression • Zero-Copy I/O",
        "metric": "Matches C Git performance with 100% memory safety; zero-copy packfile parsing via memmap2 (<14MB RSS); 10M fuzz test iterations with zero crash.",
        "tags": ["rust", "systems", "git", "posix", "compiler", "simd", "low-level", "zero-copy", "performance"]
    },
    "12_USER_SURVIVAL_MLOPS": {
        "id": 12,
        "title": "User Survival Prediction & MLOps Infrastructure Platform",
        "url": "https://github.com/KishorKumarParoi/User-Survival-Prediction",
        "stack": "Astro Airflow DAGs • Redis Low-Latency Feature Store • Alibi Detect KS Drift • Prometheus & Grafana",
        "metric": "Automated Airflow ETL to Redis Feature Store (<2ms retrieval); continuous Kolmogorov-Smirnov drift alarms; 88.9% holdout accuracy model.",
        "tags": ["airflow", "redis", "feature store", "drift", "prometheus", "grafana", "mlops", "classification"]
    },
    "13_KOOMAI_VIDEO_AI": {
        "id": 13,
        "title": "Koom-AI: Enterprise Video Intelligence & Workspace Platform",
        "url": "https://github.com/KishorKumarParoi/koom-ai",
        "stack": "Next.js 16 App Router • Manifest V3 Chrome Extension • WebRTC SVC Media Engine • Stripe Connect",
        "metric": "Sub-120ms glass-to-glass latency across 50,000+ recording minutes; 20-agent LangGraph copilot mesh; $24K MRR enterprise pilot adoption.",
        "tags": ["webrtc", "video", "fullstack", "next.js", "chrome extension", "streaming", "startup", "founder", "audio"]
    },
    "14_REINVENT_3D_PLATFORM": {
        "id": 14,
        "title": "re:invent: Interactive 3D Platform & Real-Time Visitor Telemetry",
        "url": "https://github.com/KishorKumarParoi/re-invent",
        "stack": "React 19.2 • Three.js • GSAP 3.13 • Rolldown Vite • Supabase PostgreSQL Telemetry",
        "metric": "60 FPS custom WebGL spatial camera choreography; live visitor telemetry engine with anti-tamper rate limiting serving global analytics in <100ms.",
        "tags": ["three.js", "webgl", "3d", "react", "gsap", "frontend", "vite", "supabase", "graphics"]
    },
    "15_MACOS_TAHOE_PORTFOLIO": {
        "id": 15,
        "title": "macOS Tahoe: Interactive Apple Silicon OS Portfolio in React & GSAP",
        "url": "https://github.com/KishorKumarParoi/macos-portofolio",
        "stack": "React 19 • GSAP Draggable • Minimax AI Chess Engine • Fire Particle Terminal • ATS Resume",
        "metric": "Full desktop OS recreation with fluid window stacking, minimax computer AI chess engine, interactive CLI particle terminal, and sub-100ms Edge CDN delivery.",
        "tags": ["react", "frontend", "macos", "os", "chess", "minimax", "gsap", "desktop", "ui", "ux"]
    }
}


def score_project_relevance(project: Dict[str, Any], query_text: str) -> int:
    query_lower = query_text.lower()
    score = 0
    for tag in project.get("tags", []):
        if tag in query_lower:
            score += 10
    title_words = project.get("title", "").lower().split()
    for w in title_words:
        if len(w) > 3 and w in query_lower:
            score += 5
    stack_words = project.get("stack", "").lower().split()
    for w in stack_words:
        if len(w) > 3 and w in query_lower:
            score += 4
    return score


def select_curated_project_suite(job_title: str, job_snippet: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    search_context = f"{job_title} {job_snippet}".lower()

    scored = []
    for key, p in ALL_15_PROJECTS.items():
        relevance = score_project_relevance(p, search_context)
        scored.append((relevance, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    matched = [item[1] for item in scored[:4]]

    matched_ids = {p["id"] for p in matched}
    fallback_priority = [3, 2, 1, 13]
    for fid in fallback_priority:
        if len(matched) < 4:
            cand = next((p for p in ALL_15_PROJECTS.values() if p["id"] == fid), None)
            if cand and cand["id"] not in matched_ids:
                matched.append(cand)
                matched_ids.add(cand["id"])

    cross = []
    cross_candidates = [
        ALL_15_PROJECTS["13_KOOMAI_VIDEO_AI"],
        ALL_15_PROJECTS["11_RUST_GIT_ENGINE"],
        ALL_15_PROJECTS["14_REINVENT_3D_PLATFORM"],
        ALL_15_PROJECTS["15_MACOS_TAHOE_PORTFOLIO"],
        ALL_15_PROJECTS["4_SMART_MANUFACTURING"],
        ALL_15_PROJECTS["10_REALTIME_MLOPS_KSERVE"]
    ]
    for c in cross_candidates:
        if c["id"] not in matched_ids:
            cross.append(c)
        if len(cross) >= 3:
            break

    return matched, cross


def generate_curated_cold_email(company: str, role_title: str, recipient_email: str, snippet: str = "") -> Dict[str, Any]:
    matched_projs, cross_projs = select_curated_project_suite(role_title, snippet)

    # 1. Plain Text Project Cards
    matched_text_blocks = []
    for idx, p in enumerate(matched_projs, 1):
        block = (
            f"  [{idx}] {p['title']}\n"
            f"      🔗 Code   : {p['url']}\n"
            f"      ⚙️ Stack  : {p['stack']}\n"
            f"      📈 Impact : {p['metric']}"
        )
        matched_text_blocks.append(block)
    matched_text = "\n\n".join(matched_text_blocks)

    cross_text_blocks = []
    for p in cross_projs:
        cross_text_blocks.append(f"  ▸ {p['title']}: {p['url']}\n    ↳ {p['metric']}")
    cross_text = "\n\n".join(cross_text_blocks)

    subject = f"Solving low-latency AI & Agent Infrastructure for {company} — Kishor Kumar Paroi"

    encoded_company = urllib.parse.quote(company)
    whatsapp_url = f"https://wa.me/8801724714156?text=Hi%20Kishor,%20I%20saw%20your%20pitch%20for%20{encoded_company}"
    calendly_url = "https://calendly.com/kishor-ruet-cse/15min"

    # Plain Text Body
    body = f"""Hi {company} Founding & Engineering Team,

I've been tracking {company}'s trajectory and wanted to reach out directly regarding your open {role_title} role.

I am an AI Systems Architect & Forward Deployed Engineer (Founder @ KoomAI • RUET CSE Merit Rank 483rd in Bangladesh). I specialize in high-throughput, sub-millisecond distributed AI systems and zero-trust autonomous agent meshes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 PROUD FLAGSHIP STARTUP: KoomAI (https://koom.kishor.tech)
   Enterprise 20-Agent Autonomous Mesh & Video Intelligence Powerhouse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Sub-120ms glass-to-glass WebRTC high-performance video communication & neural transcription.
• Autonomous agentic job hunter, automated candidate briefing & ATS resume tailor.
• NotebookLLM-grade deep research synthesis, multimodal document arbitration, and instant global escrow payouts.
• 24/7 personal executive assistant mesh sustaining 50,000+ recording minutes.
• 🔗 Verified Repository: https://github.com/KishorKumarParoi/koom-ai

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 4 ARCHITECTURE PROOFS MATCHED TO {role_title.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{matched_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 CROSS-DOMAIN SYSTEMS BREADTH (Proving 'Master of Many'):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{cross_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 COMPLETE 15-PROJECT PRODUCTION INDEX & RESUMES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 🌐 [ 𝒦ᵀ ] kishor.tech: https://kishor.tech (macOS Interactive Web OS)
• 𝕏 Profile: https://x.com/Mr_paroi
• Master GitHub Technical Showcase (All 15 Projects): https://github.com/KishorKumarParoi#1-flagship-technical-projects-1---15
• 38-Module AI Systems Engineering Blueprints: https://github.com/KishorKumarParoi/AI-Engineering
• 📄 1-Page Visual Resume (PDF): https://kishor.tech/resume.pdf
• 📑 2-Page ATS Dossier (PDF): https://kishor.tech/resume_single_column.pdf
• 🧊 3D Interactive Spatial Platform: https://3d.kishor.tech
• ⚡ 3D Cyber Hacker Cockpit: https://hacker.kishor.tech

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 1-CLICK INSTANT CALL (15-MIN ZOOM) OR DIRECT WHATSAPP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Direct WhatsApp Message (1-Click):
   {whatsapp_url}

📅 15-Minute Zoom Sync (Instant Calendar Booking):
   {calendly_url}

I have attached both my 1-Page Visual Resume (resume.pdf) and 2-Page Single-Column ATS Resume (resume_single_column.pdf) for immediate review.

Looking forward to taking your technical assessment or tackling a 2-week backlog bottleneck this week.

Warm regards,

Kishor Kumar Paroi
Principal AI Systems Architect | Founder @ KoomAI
B.Sc. in Computer Science & Engineering (RUET)
🌐 kishor.tech (Live macOS Workstation): https://kishor.tech
𝕏 Profile: https://x.com/Mr_paroi | GitHub: https://github.com/KishorKumarParoi
Email: kishor.ruet.cse@gmail.com | WhatsApp: +8801724714156
LinkedIn: https://linkedin.com/in/kishor-kumar-paroi-b06344166
"""

    # Responsive Modern HTML Email Version
    html_matched_cards = []
    for idx, p in enumerate(matched_projs, 1):
        card = f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #641c26; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                <span style="background-color: #641c26; color: #ffffff; padding: 2px 7px; border-radius: 4px; font-size: 12px; margin-right: 6px;">#{idx}</span>
                {p['title']}
            </div>
            <div style="margin: 4px 0;">
                <a href="{p['url']}" style="color: #2563eb; text-decoration: none; font-size: 13px; font-weight: 600;">🔗 {p['url']} &rarr;</a>
            </div>
            <div style="font-size: 12px; color: #475569; margin: 4px 0;">
                <strong style="color: #1e293b;">⚙️ Stack:</strong> {p['stack']}
            </div>
            <div style="font-size: 13px; color: #047857; font-weight: 600; margin-top: 4px;">
                <strong>📈 Impact:</strong> {p['metric']}
            </div>
        </div>
        """
        html_matched_cards.append(card)

    html_cross_cards = []
    for p in cross_projs:
        card = f"""
        <li style="margin-bottom: 8px; font-size: 13px; color: #334155;">
            <strong><a href="{p['url']}" style="color: #2563eb; text-decoration: none;">{p['title']}</a>:</strong> {p['metric']}
        </li>
        """
        html_cross_cards.append(card)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 680px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            
            <!-- kishor.tech Brand Identity Header (X & Insta Squircle Aesthetic) -->
            <div style="background: #090a0f; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 16px; margin-bottom: 22px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <!-- kishor.tech Squircle Logo (X / Insta Aesthetic) -->
                    <a href="https://kishor.tech" style="text-decoration: none; display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; background: #000000; border: 1.5px solid #334155; border-radius: 9px; box-shadow: 0 3px 8px rgba(0,0,0,0.5); text-align: center;">
                        <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 18px; font-weight: 900; color: #ffffff; letter-spacing: -1.2px;">𝒦ᵀ</span>
                    </a>
                    <div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <a href="https://kishor.tech" style="font-size: 15px; font-weight: 800; color: #f8fafc; text-decoration: none; letter-spacing: -0.2px;">
                                kishor.tech
                            </a>
                            <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8; font-size: 9px; font-weight: 700; padding: 1px 5px; border-radius: 3px; text-transform: uppercase;">LIVE OS</span>
                        </div>
                        <div style="font-size: 11px; color: #94a3b8;">
                            macOS Desktop Portfolio &bull; 15 Enterprise AI Blueprints
                        </div>
                    </div>
                </div>
                
                <!-- Social Connect Badges (X, GitHub, LinkedIn) -->
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <a href="https://x.com/Mr_paroi" style="display: inline-flex; align-items: center; gap: 4px; background: #000000; color: #ffffff; text-decoration: none; padding: 4px 9px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #334155;">
                        <span style="font-size: 12px; font-weight: 900;">𝕏</span> @Mr_paroi
                    </a>
                    <a href="https://github.com/KishorKumarParoi" style="display: inline-flex; align-items: center; gap: 4px; background: #1e293b; color: #ffffff; text-decoration: none; padding: 4px 9px; border-radius: 5px; font-size: 11px; font-weight: 700;">
                        🐙 GitHub
                    </a>
                    <a href="https://linkedin.com/in/kishor-kumar-paroi-b06344166" style="display: inline-flex; align-items: center; gap: 4px; background: #0a66c2; color: #ffffff; text-decoration: none; padding: 4px 9px; border-radius: 5px; font-size: 11px; font-weight: 700;">
                        💼 LinkedIn
                    </a>
                </div>
            </div>

            <p style="font-size: 15px; margin-top: 0;">Hi <strong>{company}</strong> Founding & Engineering Team,</p>
            
            <p style="font-size: 14px; color: #334155;">
                I've been tracking <strong>{company}</strong>'s trajectory and wanted to reach out directly regarding your open <strong>{role_title}</strong> role.
            </p>
            
            <p style="font-size: 14px; color: #334155;">
                I am an <strong>AI Systems Architect & Forward Deployed Engineer</strong> (Founder @ KoomAI &bull; B.Sc. CSE from RUET, Merit Rank 483rd in Bangladesh). I specialize in high-throughput, sub-millisecond distributed AI systems and zero-trust autonomous agent meshes:
            </p>

            <!-- KoomAI Flagship Card -->
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #ffffff; border-radius: 10px; padding: 18px 20px; margin: 20px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 18px; margin-right: 8px;">🚀</span>
                    <strong style="font-size: 16px; color: #38bdf8;">PROUD FLAGSHIP: KoomAI (<a href="https://koom.kishor.tech" style="color: #38bdf8; text-decoration: underline;">koom.kishor.tech</a>)</strong>
                </div>
                <p style="font-size: 13px; color: #94a3b8; margin: 0 0 10px 0;">Enterprise 20-Agent Autonomous Mesh & Real-Time Video Intelligence Powerhouse</p>
                <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #e2e8f0; line-height: 1.6;">
                    <li>Sub-120ms glass-to-glass WebRTC media engine across 50,000+ recording minutes</li>
                    <li>Autonomous agentic job hunter, candidate briefing & ATS resume tailor</li>
                    <li>NotebookLLM-grade deep research synthesis, multimodal document arbitration & escrow payouts</li>
                    <li>🔗 Verified Repository: <a href="https://github.com/KishorKumarParoi/koom-ai" style="color: #67e8f9;">github.com/KishorKumarParoi/koom-ai</a></li>
                </ul>
            </div>

            <!-- Matched 4 Projects Header -->
            <div style="margin-top: 24px; margin-bottom: 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px;">
                <span style="font-size: 14px; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;">
                    ⚡ 4 Architecture Proofs Matched to {role_title}:
                </span>
            </div>
            
            {''.join(html_matched_cards)}

            <!-- Cross-Domain Breadth -->
            <div style="margin-top: 22px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px;">
                <strong style="font-size: 13px; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;">🌐 Cross-Domain Systems Breadth ('Master of Many'):</strong>
                <ul style="margin: 8px 0 0 0; padding-left: 18px; line-height: 1.5;">
                    {''.join(html_cross_cards)}
                </ul>
            </div>

            <!-- Verified Credentials Bar -->
            <div style="margin-top: 22px; padding: 14px 18px; background-color: #f1f5f9; border-radius: 8px; font-size: 13px;">
                <strong style="color: #0f172a;">📚 Complete 15-Project Index & Live Credentials:</strong>
                <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px;">
                    <a href="https://kishor.tech" style="background-color: #000000; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; border: 1px solid #334155;"><strong>𝒦ᵀ</strong> kishor.tech (Live OS)</a>
                    <a href="https://x.com/Mr_paroi" style="background-color: #000000; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; border: 1px solid #334155;"><strong>𝕏</strong> @Mr_paroi</a>
                    <a href="https://github.com/KishorKumarParoi#1-flagship-technical-projects-1---15" style="background-color: #0f172a; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">🐙 All 15 Projects on GitHub</a>
                    <a href="https://kishor.tech/resume.pdf" style="background-color: #641c26; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📄 1-Page Visual Resume</a>
                    <a href="https://kishor.tech/resume_single_column.pdf" style="background-color: #1e293b; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">📑 2-Page ATS Dossier</a>
                    <a href="https://3d.kishor.tech" style="background-color: #4338ca; color: #ffffff; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px;">🧊 3D Platform</a>
                </div>
            </div>

            <!-- Zero-Friction CTA Buttons -->
            <div style="margin-top: 28px; padding: 20px; background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 10px; text-align: center;">
                <div style="font-size: 14px; font-weight: 700; color: #581c87; margin-bottom: 12px; text-transform: uppercase;">
                    ⚡ Zero-Friction Direct Connect
                </div>
                <div style="display: inline-block; margin: 4px;">
                    <a href="{whatsapp_url}" style="background-color: #25D366; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 13px; display: inline-block;">
                        💬 Message on WhatsApp (1-Click)
                    </a>
                </div>
                <div style="display: inline-block; margin: 4px;">
                    <a href="{calendly_url}" style="background-color: #0284c7; color: #ffffff; padding: 12px 22px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 13px; display: inline-block;">
                        📅 Book 15-Min Zoom Call
                    </a>
                </div>
                <p style="font-size: 12px; color: #6b21a8; margin-top: 10px; margin-bottom: 0;">
                    Both <strong>1-Page Visual Resume</strong> & <strong>2-Page ATS Dossier</strong> are attached to this email.
                </p>
            </div>

            <!-- Signature -->
            <div style="margin-top: 26px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 13px; color: #475569;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <a href="https://kishor.tech" style="text-decoration: none; display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; background: #000000; border-radius: 6px; color: #ffffff; font-weight: 900; font-size: 13px; border: 1px solid #334155; text-align: center;">𝒦ᵀ</a>
                    <strong style="font-size: 15px; color: #0f172a;">Kishor Kumar Paroi</strong>
                </div>
                Principal AI Systems Architect | Founder @ KoomAI<br>
                B.Sc. in Computer Science & Engineering (RUET)<br>
                <div style="margin-top: 6px; color: #64748b;">
                    <a href="https://kishor.tech" style="color: #0f172a; font-weight: 700; text-decoration: underline;">kishor.tech</a> &bull; 
                    <a href="https://x.com/Mr_paroi" style="color: #0f172a; text-decoration: none; font-weight: 700;">𝕏 @Mr_paroi</a> &bull; 
                    Email: <a href="mailto:kishor.ruet.cse@gmail.com" style="color: #2563eb;">kishor.ruet.cse@gmail.com</a> &bull; 
                    WhatsApp: <a href="https://wa.me/8801724714156" style="color: #16a34a; font-weight: 600;">+8801724714156</a> &bull; 
                    <a href="https://linkedin.com/in/kishor-kumar-paroi-b06344166" style="color: #0a66c2; font-weight: 600;">LinkedIn</a>
                </div>
            </div>

        </div>
    </body>
    </html>
    """

    mailto_params = urllib.parse.urlencode({"subject": subject, "body": body}, quote_via=urllib.parse.quote)
    mailto_url = f"mailto:{recipient_email}?{mailto_params}"

    return {
        "to": recipient_email,
        "subject": subject,
        "body": body,
        "html_body": html_body,
        "mailto_url": mailto_url,
        "matched_projects": matched_projs,
        "cross_projects": cross_projs
    }


if __name__ == "__main__":
    print(f"Loaded all {len(ALL_15_PROJECTS)} verified projects with Eye-Catching Dual Plain/HTML formatting!")
    sample = generate_curated_cold_email("Anthropic", "Senior vLLM & LLMOps Systems Engineer", "founders@anthropic.com", "High-throughput inference on GPU clusters with vLLM, Rust and LangGraph agents")
    print(f"Generated Subject: {sample['subject']}\n")
    print("--- SAMPLE PLAIN TEXT PREVIEW ---")
    print(sample["body"][:900] + "\n...")
    print("\n--- SAMPLE HTML LENGTH ---")
    print(f"{len(sample['html_body'])} characters of rich responsive HTML styling!")
