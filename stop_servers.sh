#!/bin/bash

# AI Medical A2A Consultation System - Server Stop Script
# 전체 시스템 서버 중지 스크립트

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

echo -e "${WHITE}🛑 AI Medical A2A Consultation System 중지${NC}"
echo -e "${WHITE}================================================${NC}"

# PID 파일을 이용한 정확한 프로세스 종료
stop_server() {
    local name=$1
    local pidfile=$2
    local color=$3
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${color}🛑 $name 서버 중지 중... (PID: $pid)${NC}"
            kill -TERM "$pid" 2>/dev/null
            
            # 정상 종료 대기 (최대 10초)
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 여전히 실행 중이면 강제 종료
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}⚠️ 강제 종료: $name${NC}"
                kill -KILL "$pid" 2>/dev/null
            fi
            
            echo -e "${GREEN}✅ $name 서버 중지됨${NC}"
        else
            echo -e "${YELLOW}⚠️ $name 서버가 이미 중지됨${NC}"
        fi
        rm -f "$pidfile"
    else
        echo -e "${YELLOW}⚠️ $name PID 파일이 없음${NC}"
    fi
}

# 각 서버 중지
stop_server "Flask 웹 서버" "pids/web.pid" "$WHITE"
stop_server "Orchestrator API" "pids/orchestrator.pid" "$CYAN"
stop_server "DR_PROSTATE API" "pids/prostate.pid" "$PURPLE"
stop_server "DR_BLADDER API" "pids/bladder.pid" "$BLUE"

# 프로세스명으로 추가 정리
echo -e "${YELLOW}🧹 남은 프로세스 정리 중...${NC}"
pkill -f "main_bladder.py" 2>/dev/null || true
pkill -f "main_prostate.py" 2>/dev/null || true
pkill -f "main_orchestrator.py" 2>/dev/null || true
pkill -f "web.*app.py" 2>/dev/null || true

# 포트 사용 확인
echo -e "${WHITE}🔍 포트 사용 상태 확인...${NC}"
for port in 8000 8001 8002 8003; do
    if lsof -i :$port 2>/dev/null | grep -q LISTEN; then
        echo -e "${RED}❌ 포트 $port: 여전히 사용 중${NC}"
    else
        echo -e "${GREEN}✅ 포트 $port: 해제됨${NC}"
    fi
done

# 임시 파일 정리
echo -e "${YELLOW}🗂️ 임시 파일 정리 중...${NC}"
rm -rf pids/*.pid 2>/dev/null || true

echo -e "${WHITE}================================================${NC}"
echo -e "${GREEN}🎉 AI Medical A2A 시스템이 완전히 중지되었습니다!${NC}"
echo -e "${WHITE}================================================${NC}"

echo -e "${WHITE}다시 시작하려면: ${YELLOW}./start_servers.sh${NC}"