#!/usr/bin/env bash
# Fnomo Decision Engine — Start All Services
set -e

FNOMO_ROOT="$(cd "$(dirname "$0")" && pwd)"
COUNCIL_DIR="$FNOMO_ROOT/llm-council"
G0DM0D3_DIR="$FNOMO_ROOT/G0DM0D3"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   FNOMO ENTERPRISE DECISION ENGINE       ║"
echo "║   G0DM0D3 + LLM Council + Kimi K2.5     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. LLM Council Backend ──────────────────────────────────────
echo "[1/3] Starting LLM Council backend (FastAPI)..."
cd "$COUNCIL_DIR"
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload &
COUNCIL_PID=$!
echo "      Council API → http://127.0.0.1:8001  (PID $COUNCIL_PID)"

# ── 2. LLM Council Frontend ─────────────────────────────────────
echo "[2/3] Starting LLM Council frontend (Next.js)..."
cd "$COUNCIL_DIR/frontend"
npm run dev -- --port 3001 &
FRONTEND_PID=$!
echo "      Council UI  → http://localhost:3001  (PID $FRONTEND_PID)"

# ── 3. G0DM0D3 Static Server ────────────────────────────────────
echo "[3/3] Serving G0DM0D3 exploration engine..."
cd "$G0DM0D3_DIR"
python -m http.server 8080 &
G0DM0D3_PID=$!
echo "      G0DM0D3 UI  → http://localhost:8080  (PID $G0DM0D3_PID)"

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│  All services running.                  │"
echo "│                                         │"
echo "│  G0DM0D3 (Exploration)                  │"
echo "│  → http://localhost:8080                │"
echo "│                                         │"
echo "│  LLM Council (Consensus)                │"
echo "│  → http://localhost:3001                │"
echo "│                                         │"
echo "│  CLI engine:                            │"
echo "│  python fnomo_engine.py \"<task>\"        │"
echo "│                                         │"
echo "│  Press Ctrl+C to stop all.              │"
echo "└─────────────────────────────────────────┘"
echo ""

trap "echo 'Stopping...'; kill $COUNCIL_PID $FRONTEND_PID $G0DM0D3_PID 2>/dev/null; exit 0" INT TERM
wait
