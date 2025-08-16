#!/bin/bash
# DR_PROSTATE API 실행 스크립트

echo "Starting DR_PROSTATE API on port 8002..."
cd "$(dirname "$0")"
uvicorn main_prostate:app --reload --port 8002 --host 0.0.0.0