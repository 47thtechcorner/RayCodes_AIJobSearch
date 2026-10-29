#!/usr/bin/env bash
# ==============================================================================
# One-Go Automated Job Outreach & Email Dispatcher
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_BIN="python3"

echo "========================================================================"
echo "🚀 ONE-GO AUTOMATED JOB ACCUMULATION & EMAIL DISPATCHER"
echo "========================================================================"
echo ""
echo "Select outreach channel:"
echo "  1) All Platforms (Twitter, Toptal, LinkedIn, YC, Remote Portals)"
echo "  2) Twitter / 𝕏 Founder Posts Only"
echo "  3) Toptal & Elite Networks Only ($150k - $300k+)"
echo "  4) LinkedIn Engineering Applications Only"
echo "  5) Y Combinator & Hacker News Startups Only"
echo "  6) Re-accumulate and Categorize all JSON files only"
echo ""

MODE="${1:-}"
PLATFORM="all"

case "$MODE" in
  twitter|x|2)
    PLATFORM="twitter"
    ;;
  toptal|3)
    PLATFORM="toptal"
    ;;
  linkedin|4)
    PLATFORM="linkedin"
    ;;
  yc|5)
    PLATFORM="yc"
    ;;
  accumulate|clean|6)
    echo "⚙️ Running Job Accumulation & Categorization across all JSON files..."
    "$PY_BIN" "$SCRIPT_DIR/scripts/accumulate_and_categorize_jobs.py"
    exit 0
    ;;
  *)
    PLATFORM="all"
    ;;
esac

# Accumulate and refresh categories first
"$PY_BIN" "$SCRIPT_DIR/scripts/accumulate_and_categorize_jobs.py"

# Run One-Go Dispatcher
shift || true
echo ""
echo "🚀 Starting One-Go Dispatcher for [$PLATFORM]..."
"$PY_BIN" "$SCRIPT_DIR/scripts/one_go_dispatcher.py" --platform "$PLATFORM" "$@"
