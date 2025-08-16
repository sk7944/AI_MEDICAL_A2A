#!/bin/bash
# DR_BLADDER API 실행 스크립트

echo "Starting DR_BLADDER API on port 8001..."
cd "$(dirname "$0")"
uvicorn main_bladder:app --reload --port 8001 --host 0.0.0.0