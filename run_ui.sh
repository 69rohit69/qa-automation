#!/usr/bin/env bash
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
if [[ ! -f .env ]]; then
  echo "Create .env from .env.example and set GEMINI_API_KEY"
  exit 1
fi
.venv/bin/streamlit run app.py
