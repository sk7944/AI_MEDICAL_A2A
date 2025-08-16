#!/bin/bash

# AI Medical A2A Consultation System - Server Status Check Script
# 전체 시스템 서버 상태 확인 스크립트

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

echo -e "${WHITE}📊 AI Medical A2A Consultation System 상태 확인${NC}"
echo -e "${WHITE}================================================${NC}"

# 현재 시간 표시
echo -e "${WHITE}🕐 확인 시간: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# 프로세스 상태 확인
check_process() {
    local name=$1
    local pidfile=$2
    local color=$3
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${color}✅ $name: 실행 중 (PID: $pid)${NC}"
            return 0
        else
            echo -e "${RED}❌ $name: PID 파일 있지만 프로세스 없음 ($pid)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $name: PID 파일 없음${NC}"
        return 1
    fi
}

# 포트 연결 확인
check_port() {
    local port=$1
    local name=$2
    local endpoint=$3
    local color=$4
    
    if curl -s --max-time 5 "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo -e "${color}✅ $name (포트 $port): 응답 정상${NC}"
        return 0
    else
        echo -e "${RED}❌ $name (포트 $port): 응답 없음${NC}"
        return 1
    fi
}

# 프로세스 상태 확인
echo -e "${WHITE}🔍 프로세스 상태:${NC}"
check_process "DR_BLADDER API" "pids/bladder.pid" "$BLUE"
check_process "DR_PROSTATE API" "pids/prostate.pid" "$PURPLE"
check_process "Orchestrator API" "pids/orchestrator.pid" "$CYAN"
check_process "Flask 웹 서버" "pids/web.pid" "$WHITE"

echo ""

# 포트 연결 상태 확인
echo -e "${WHITE}🌐 포트 연결 상태:${NC}"
check_port 8001 "DR_BLADDER API" "/health" "$BLUE"
check_port 8002 "DR_PROSTATE API" "/health" "$PURPLE"
check_port 8003 "Orchestrator API" "/health" "$CYAN"
check_port 5000 "Flask 웹 서버" "/" "$WHITE"

echo ""

# Ollama 서버 확인
echo -e "${WHITE}🤖 Ollama 서버 상태:${NC}"
if curl -s --max-time 5 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama 서버: 정상 동작${NC}"
    
    # gemma3:4b 모델 확인
    if ollama list 2>/dev/null | grep -q "gemma3:4b"; then
        echo -e "${GREEN}✅ gemma3:4b 모델: 사용 가능${NC}"
    else
        echo -e "${YELLOW}⚠️ gemma3:4b 모델: 설치 필요${NC}"
    fi
else
    echo -e "${RED}❌ Ollama 서버: 연결 실패${NC}"
fi

echo ""

# 최근 로그 확인
echo -e "${WHITE}📋 최근 로그 상태:${NC}"
for logfile in logs/*.log; do
    if [ -f "$logfile" ]; then
        local basename=$(basename "$logfile" .log)
        local lines=$(wc -l < "$logfile" 2>/dev/null || echo "0")
        local size=$(du -h "$logfile" 2>/dev/null | cut -f1 || echo "0B")
        echo -e "${YELLOW}📄 $basename.log: $lines 줄, $size${NC}"
    fi
done

echo ""

# 전체 시스템 상태 요약
all_running=true

# API 서버들 확인
for port in 8001 8002 8003 5000; do
    if ! lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        all_running=false
        break
    fi
done

echo -e "${WHITE}================================================${NC}"
if [ "$all_running" = true ]; then
    echo -e "${GREEN}🎉 시스템 상태: 모든 서버가 정상 동작 중${NC}"
    echo -e "${WHITE}📱 웹 인터페이스: ${CYAN}http://localhost:5000${NC}"
else
    echo -e "${RED}⚠️ 시스템 상태: 일부 서버에 문제가 있습니다${NC}"
    echo -e "${WHITE}🔧 문제 해결: ${YELLOW}./restart_servers.sh${NC}"
fi
echo -e "${WHITE}================================================${NC}"