"""
DR_PROSTATE API Server
FastAPI wrapper for DR_PROSTATE logic
Port: 8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import logging
import uvicorn

# DR_PROSTATE 로직 임포트
from prostate_logic import analyze_prostate_question

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="DR_PROSTATE API",
    description="Prostate Diseases Medical AI Assistant API",
    version="1.0.0"
)

# CORS 설정 (n8n 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # n8n 및 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response 모델
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    agent: str = "DR_PROSTATE"
    answer: str

class HealthResponse(BaseModel):
    status: str
    agent: str
    message: str

# 엔드포인트
@app.get("/")
async def root() -> Dict[str, str]:
    """루트 엔드포인트"""
    return {
        "agent": "DR_PROSTATE",
        "message": "Prostate Diseases Medical AI Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "ask": "POST /ask",
            "health": "GET /health"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """헬스체크 엔드포인트"""
    try:
        # Ollama 연결 테스트
        from prostate_logic import ProstateAnalyzer
        analyzer = ProstateAnalyzer()
        
        if analyzer.validate_ollama_connection():
            return HealthResponse(
                status="healthy",
                agent="DR_PROSTATE",
                message="Service is running and Ollama is connected"
            )
        else:
            return HealthResponse(
                status="degraded",
                agent="DR_PROSTATE",
                message="Service is running but Ollama connection failed"
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            agent="DR_PROSTATE",
            message=f"Health check failed: {str(e)}"
        )

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest) -> AnswerResponse:
    """
    전립선 관련 질문 처리 엔드포인트
    
    Args:
        request: 질문 요청 객체
        
    Returns:
        DR_PROSTATE의 응답
    """
    try:
        # 질문 유효성 검증
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Received question: {request.question[:100]}...")
        
        # DR_PROSTATE 로직 호출
        answer = analyze_prostate_question(request.question)
        
        logger.info("Successfully generated response")
        
        return AnswerResponse(
            agent="DR_PROSTATE",
            answer=answer
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/model-info")
async def get_model_info() -> Dict[str, Any]:
    """모델 정보 조회 엔드포인트"""
    try:
        from prostate_logic import ProstateAnalyzer
        analyzer = ProstateAnalyzer()
        return {
            "agent": "DR_PROSTATE",
            "model": analyzer.get_model_info()
        }
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

# 서버 실행 코드
if __name__ == "__main__":
    # uvicorn main_prostate:app --reload --port 8002
    uvicorn.run(
        "main_prostate:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )