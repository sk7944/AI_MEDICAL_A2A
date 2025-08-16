"""
Medical Orchestrator API Server
DR_BLADDER와 DR_PROSTATE를 통합하여 종합적인 의료 상담을 제공하는 API 서버
Port: 8003
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import uvicorn
import asyncio
from datetime import datetime

# 오케스트레이터 로직 임포트
from orchestrator_logic import MedicalOrchestrator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="Medical Consultation Orchestrator API",
    description="AI Medical A2A Consultation System - 전문 AI 에이전트들을 통합한 의료 상담 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 글로벌 오케스트레이터 인스턴스
orchestrator = MedicalOrchestrator()

# Request/Response 모델
class ConsultationRequest(BaseModel):
    question: str

class ConsultationResponse(BaseModel):
    consultation_id: str
    question: str
    individual_consultations: Dict[str, Any]
    synthesized_consultation: str
    consultation_timestamp: str
    orchestrator_info: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    agents: Dict[str, Any]
    orchestrator_info: Dict[str, Any]

class StatusUpdate(BaseModel):
    timestamp: str
    agent: str
    status: str
    message: str

# 진행 상황 추적을 위한 임시 저장소
consultation_progress = {}

# 엔드포인트
@app.get("/")
async def root() -> Dict[str, Any]:
    """루트 엔드포인트"""
    return {
        "service": "Medical Consultation Orchestrator",
        "description": "AI Medical A2A Consultation System",
        "version": "1.0.0",
        "agents": {
            "bladder": "DR_BLADDER (port 8001)",
            "prostate": "DR_PROSTATE (port 8002)",
            "orchestrator": "Medical Orchestrator (port 8003)"
        },
        "endpoints": {
            "consult": "POST /consult",
            "health": "GET /health",
            "agents": "GET /agents",
            "progress": "GET /progress/{consultation_id}"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """전체 시스템 헬스체크"""
    try:
        logger.info("🏥 전체 시스템 헬스체크 시작...")
        health_data = orchestrator.check_all_agents_health()
        
        # 전체 시스템 상태 결정
        overall_status = "healthy"
        for agent, status in health_data.items():
            if status.get("status") == "unhealthy":
                overall_status = "unhealthy"
                break
            elif status.get("status") == "degraded":
                overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            agents=health_data,
            orchestrator_info={
                "model": orchestrator.model_name,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
        )
    except Exception as e:
        logger.error(f"❌ 헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/agents")
async def get_agents_status() -> Dict[str, Any]:
    """개별 에이전트 상태 조회"""
    try:
        return orchestrator.check_all_agents_health()
    except Exception as e:
        logger.error(f"❌ 에이전트 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents status: {str(e)}")

def add_progress_update(consultation_id: str, agent: str, status: str, message: str):
    """진행 상황 업데이트 추가"""
    if consultation_id not in consultation_progress:
        consultation_progress[consultation_id] = []
    
    consultation_progress[consultation_id].append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "status": status,
        "message": message
    })

@app.get("/progress/{consultation_id}")
async def get_consultation_progress(consultation_id: str) -> List[StatusUpdate]:
    """상담 진행 상황 조회"""
    if consultation_id not in consultation_progress:
        raise HTTPException(status_code=404, detail="Consultation ID not found")
    
    return [StatusUpdate(**update) for update in consultation_progress[consultation_id]]

@app.post("/consult")
async def medical_consultation(request: ConsultationRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    종합 의료 상담 엔드포인트
    
    Args:
        request: 상담 요청 (질문 포함)
        
    Returns:
        종합 의료 상담 결과
    """
    try:
        # 질문 유효성 검증
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # 상담 ID 생성
        consultation_id = f"consultation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🚀 새로운 의료 상담 시작: {consultation_id}")
        logger.info(f"📝 질문: {request.question[:100]}...")
        
        # 진행 상황 초기화
        add_progress_update(consultation_id, "ORCHESTRATOR", "started", "의료 상담을 시작합니다")
        add_progress_update(consultation_id, "ORCHESTRATOR", "querying", "전문 에이전트들에게 질의를 보내는 중...")
        
        # 전체 상담 프로세스 실행
        result = await orchestrator.full_consultation(request.question)
        
        # 상담 ID 추가
        result["consultation_id"] = consultation_id
        
        # 진행 상황 업데이트
        if "error" in result:
            add_progress_update(consultation_id, "ORCHESTRATOR", "error", f"상담 중 오류 발생: {result['error']}")
        else:
            add_progress_update(consultation_id, "DR_BLADDER", "completed", "방광 전문가 상담 완료")
            add_progress_update(consultation_id, "DR_PROSTATE", "completed", "전립선 전문가 상담 완료")
            add_progress_update(consultation_id, "ORCHESTRATOR", "synthesizing", "전문가 의견을 종합하는 중...")
            add_progress_update(consultation_id, "ORCHESTRATOR", "completed", "종합 의료 상담이 완료되었습니다")
        
        logger.info(f"✅ 의료 상담 완료: {consultation_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 의료 상담 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Medical consultation failed: {str(e)}")

@app.get("/model-info")
async def get_model_info() -> Dict[str, Any]:
    """오케스트레이터 모델 정보 조회"""
    try:
        return {
            "orchestrator": {
                "model": orchestrator.model_name,
                "version": "1.0.0",
                "type": "Medical Consultation Orchestrator"
            },
            "integrated_agents": {
                "bladder": "DR_BLADDER - 방광암 전문 AI",
                "prostate": "DR_PROSTATE - 전립선 질환 전문 AI"
            },
            "capabilities": [
                "Multi-agent medical consultation",
                "Parallel agent querying",
                "Medical opinion synthesis",
                "Real-time progress tracking"
            ]
        }
    except Exception as e:
        logger.error(f"❌ 모델 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# 서버 실행 코드
if __name__ == "__main__":
    # uvicorn main_orchestrator:app --reload --port 8003
    uvicorn.run(
        "main_orchestrator:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )