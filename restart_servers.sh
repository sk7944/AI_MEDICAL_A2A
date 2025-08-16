#!/bin/bash

# AI Medical A2A Consultation System - Server Restart Script
# 전체 시스템 서버 재시작 스크립트

# 색상 정의
WHITE='\033[1;37m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${WHITE}🔄 AI Medical A2A Consultation System 재시작${NC}"
echo -e "${WHITE}================================================${NC}"

# 1단계: 기존 서버들 중지
echo -e "${YELLOW}1️⃣ 기존 서버들 중지 중...${NC}"
./stop_servers.sh

echo ""
echo -e "${YELLOW}⏳ 시스템 정리를 위해 5초 대기...${NC}"
sleep 5

# 2단계: 서버들 재시작
echo -e "${YELLOW}2️⃣ 서버들 재시작 중...${NC}"
./start_servers.sh

echo -e "${GREEN}🎉 AI Medical A2A 시스템 재시작 완료!${NC}"