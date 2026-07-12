#!/bin/bash
# Script para arrancar la API de Agentic Sales
cd "$(dirname "$0")"

PYTHONPATH=app .venv/bin/python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
