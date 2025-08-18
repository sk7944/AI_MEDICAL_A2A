#!/bin/bash

# AI Medical A2A Consultation System - Server Startup Script
# 전체 시스템 서버 시작 스크립트

set -e  # 오류 발생 시 스크립트 중지

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${WHITE}🚀 AI Medical A2A Consultation System 시작${NC}"
echo -e "${WHITE}================================================${NC}"

# 가상환경 확인
if [ ! -d "env" ]; then
    echo -e "${RED}❌ 가상환경이 없습니다. env 디렉토리를 확인해주세요.${NC}"
    exit 1
fi

# Ollama 서버 확인
echo -e "${CYAN}🔍 Ollama 서버 상태 확인 중...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${RED}❌ Ollama 서버가 실행되지 않았습니다.${NC}"
    echo -e "${YELLOW}💡 Ollama를 먼저 실행해주세요: ollama serve${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Ollama 서버 연결 확인${NC}"

# gemma3:4b 모델 확인
echo -e "${CYAN}🔍 gemma3:4b 모델 확인 중...${NC}"
if ! ollama list | grep -q "gemma3:4b"; then
    echo -e "${YELLOW}⚠️ gemma3:4b 모델이 없습니다. 설치 중...${NC}"
    ollama pull gemma3:4b
fi
echo -e "${GREEN}✅ gemma3:4b 모델 확인 완료${NC}"

# 기존 프로세스 정리
echo -e "${YELLOW}🧹 기존 서버 프로세스 정리 중...${NC}"
pkill -f "main_bladder.py" 2>/dev/null || true
pkill -f "main_prostate.py" 2>/dev/null || true  
pkill -f "main_orchestrator.py" 2>/dev/null || true
pkill -f "web.*app.py" 2>/dev/null || true
sleep 2

# 로그 디렉토리 생성
mkdir -p logs

# PID 파일 디렉토리 생성
mkdir -p pids

echo -e "${WHITE}📡 서버들을 순차적으로 시작합니다...${NC}"

# 1. DR_BLADDER API 서버 시작 (포트 8001)
echo -e "${BLUE}🫧 DR_BLADDER API 서버 시작 중... (포트 8001)${NC}"
cd agents/bladder
nohup python main_bladder.py > ../../logs/bladder.log 2>&1 & 
BLADDER_PID=$!
echo $BLADDER_PID > ../../pids/bladder.pid
cd ../..
echo -e "${GREEN}✅ DR_BLADDER 서버 시작됨 (PID: $BLADDER_PID)${NC}"

# 서버 준비 대기
sleep 5

# 2. DR_PROSTATE API 서버 시작 (포트 8002)
echo -e "${PURPLE}🫐 DR_PROSTATE API 서버 시작 중... (포트 8002)${NC}"
cd agents/prostate
nohup python main_prostate.py > ../../logs/prostate.log 2>&1 &
PROSTATE_PID=$!
echo $PROSTATE_PID > ../../pids/prostate.pid
cd ../..
echo -e "${GREEN}✅ DR_PROSTATE 서버 시작됨 (PID: $PROSTATE_PID)${NC}"

# 서버 준비 대기
sleep 5

# 3. Orchestrator API 서버 시작 (포트 8003)
echo -e "${CYAN}🎭 Orchestrator API 서버 시작 중... (포트 8003)${NC}"
cd orchestrator
nohup python main_orchestrator.py > ../logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > ../pids/orchestrator.pid
cd ..
echo -e "${GREEN}✅ Orchestrator 서버 시작됨 (PID: $ORCHESTRATOR_PID)${NC}"

# 서버 준비 대기
sleep 5

# 4. Flask 웹 서버 시작 (포트 8000)
echo -e "${WHITE}🌐 Flask 웹 서버 시작 중... (포트 8000)${NC}"
cd web
nohup ../env/bin/python app.py > ../logs/web.log 2>&1 &
WEB_PID=$!
echo $WEB_PID > ../pids/web.pid
cd ..
echo -e "${GREEN}✅ Flask 웹 서버 시작됨 (PID: $WEB_PID)${NC}"

# 서버 상태 확인
echo -e "${WHITE}🔍 서버 상태 확인 중...${NC}"
sleep 10

# 포트 연결 확인
check_port() {
    local port=$1
    local name=$2
    local color=$3
    
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "${color}✅ $name (포트 $port): 정상 동작${NC}"
        return 0
    else
        echo -e "${RED}❌ $name (포트 $port): 연결 실패${NC}"
        return 1
    fi
}

# 각 서버 상태 확인
echo -e "${WHITE}📊 서버 상태 체크:${NC}"
check_port 8001 "DR_BLADDER API" "$BLUE"
check_port 8002 "DR_PROSTATE API" "$PURPLE" 
check_port 8003 "Orchestrator API" "$CYAN"

# Flask 웹 서버는 다른 방식으로 확인
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${WHITE}✅ Flask 웹 서버 (포트 8000): 정상 동작${NC}"
else
    echo -e "${RED}❌ Flask 웹 서버 (포트 8000): 연결 실패${NC}"
fi

echo -e "${WHITE}================================================${NC}"
echo -e "${GREEN}🎉 AI Medical A2A 시스템이 성공적으로 시작되었습니다!${NC}"
echo -e "${WHITE}================================================${NC}"

echo -e "${WHITE}📱 접속 URL:${NC}"
echo -e "   🏠 메인 페이지: ${CYAN}http://localhost:8000${NC}"
echo -e "   💬 의료 상담: ${CYAN}http://localhost:8000/consult${NC}"
echo -e "   🏥 시스템 상태: ${CYAN}http://localhost:8000/health${NC}"
echo -e "   📋 소개: ${CYAN}http://localhost:8000/about${NC}"

echo -e "${WHITE}🔧 API 엔드포인트:${NC}"
echo -e "   ${BLUE}DR_BLADDER API: http://localhost:8001${NC}"
echo -e "   ${PURPLE}DR_PROSTATE API: http://localhost:8002${NC}"
echo -e "   ${CYAN}Orchestrator API: http://localhost:8003${NC}"

echo -e "${WHITE}📋 관리 명령어:${NC}"
echo -e "   로그 확인: ${YELLOW}tail -f logs/[bladder|prostate|orchestrator|web].log${NC}"
echo -e "   서버 중지: ${YELLOW}./stop_servers.sh${NC}"
echo -e "   서버 재시작: ${YELLOW}./restart_servers.sh${NC}"

echo -e "${WHITE}================================================${NC}"
echo -e "${GREEN}시스템이 준비되었습니다. 브라우저에서 http://localhost:8000 에 접속하세요!${NC}"