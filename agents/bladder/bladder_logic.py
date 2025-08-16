"""
DR_BLADDER Agent - Core Logic Module
방광암 관련 의료 질문 분석 및 응답 생성
"""

import ollama
import json
import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.shared.vector_db import get_vector_db

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BladderAnalyzer:
    """방광암 전문 의료 분석기"""
    
    def __init__(self, model_name: str = "gemma3:4b"):
        """
        초기화
        Args:
            model_name: Ollama 모델 이름 (기본: gemma3:4b)
        """
        self.model_name = model_name
        self.system_prompt = self._get_system_prompt()
        
        # 벡터 DB 초기화
        try:
            self.vector_db = get_vector_db()
            logger.info("Vector DB initialized for bladder guidelines")
        except Exception as e:
            logger.warning(f"Vector DB initialization failed: {e}")
            self.vector_db = None
        
    def _get_system_prompt(self) -> str:
        """시스템 프롬프트 정의"""
        return """You are DR_BLADDER, a specialized medical AI assistant focused on bladder cancer.
        
Your expertise includes:
- Bladder cancer diagnosis and staging
- Treatment options (BCG therapy, chemotherapy, surgical interventions)
- Risk factors and prevention
- Patient care and follow-up protocols
- Latest research and clinical guidelines

Guidelines:
1. Provide evidence-based medical information
2. Use appropriate medical terminology with explanations
3. Consider patient safety and emphasize professional consultation
4. Structure responses clearly with sections when appropriate
5. Include relevant statistics and success rates when available

Remember: Always recommend consultation with healthcare professionals for personal medical decisions."""

    def analyze_bladder_question(self, question: str) -> str:
        """
        방광암 관련 질문 분석 및 응답 생성
        
        Args:
            question: 사용자의 의료 질문
            
        Returns:
            전문적인 의료 응답
            
        Raises:
            Exception: Ollama 서버 연결 실패 또는 모델 오류
        """
        try:
            # 입력 검증
            if not question or not question.strip():
                return "질문을 입력해주세요."
            
            logger.info(f"분석 시작: {question[:50]}...")
            
            # RAG: 관련 가이드라인 검색
            context = ""
            if self.vector_db:
                try:
                    context = self.vector_db.get_context_for_prompt(
                        query=question,
                        source_type="bladder",
                        n_results=3
                    )
                    if context:
                        logger.info("Retrieved context from bladder cancer guidelines")
                    else:
                        logger.info("No relevant context found in guidelines")
                except Exception as e:
                    logger.warning(f"Context retrieval failed: {e}")
            
            # 프롬프트 구성 (RAG 통합)
            if context:
                full_prompt = f"""{self.system_prompt}

{context}

Question: {question}

Based on the EAU bladder cancer guidelines provided above, provide a comprehensive medical response:"""
            else:
                full_prompt = f"{self.system_prompt}\n\nQuestion: {question}\n\nProvide a comprehensive medical response:"
            
            # Ollama 모델 호출
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': self.system_prompt
                    },
                    {
                        'role': 'user',
                        'content': question
                    }
                ],
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 2048
                }
            )
            
            # 응답 추출
            if response and 'message' in response:
                answer = response['message']['content']
                logger.info("분석 완료")
                return self._format_response(answer, question)
            else:
                logger.error("모델 응답 형식 오류")
                return "응답 생성 중 오류가 발생했습니다."
                
        except ollama.ResponseError as e:
            logger.error(f"Ollama 응답 오류: {e}")
            return f"모델 응답 오류: {str(e)}"
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return f"시스템 오류가 발생했습니다: {str(e)}"
    
    def _format_response(self, answer: str, question: str) -> str:
        """
        응답 포맷팅
        
        Args:
            answer: 원본 응답
            question: 원본 질문
            
        Returns:
            포맷된 응답
        """
        # 응답에 필수 경고 문구 추가
        disclaimer = "\n\n⚠️ **의학적 주의사항**: 이 정보는 교육 목적으로만 제공됩니다. 실제 진단과 치료는 반드시 전문 의료진과 상담하시기 바랍니다."
        
        # 질문 유형 분석
        if any(keyword in question.lower() for keyword in ['진단', 'diagnosis', '증상', 'symptom']):
            prefix = "📋 **진단 관련 정보**\n\n"
        elif any(keyword in question.lower() for keyword in ['치료', 'treatment', 'therapy', 'bcg']):
            prefix = "💊 **치료 관련 정보**\n\n"
        elif any(keyword in question.lower() for keyword in ['예방', 'prevention', '위험', 'risk']):
            prefix = "🛡️ **예방 및 위험 요인**\n\n"
        else:
            prefix = "🏥 **의료 정보**\n\n"
        
        return prefix + answer + disclaimer
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 반환
        
        Returns:
            모델 상태 및 정보
        """
        try:
            # Ollama 모델 정보 조회
            models = ollama.list()
            model_info = {
                'model_name': self.model_name,
                'status': 'unknown',
                'size': 'unknown'
            }
            
            for model in models.get('models', []):
                if self.model_name in model.get('name', ''):
                    model_info['status'] = 'available'
                    model_info['size'] = model.get('size', 'unknown')
                    break
            
            return model_info
            
        except Exception as e:
            logger.error(f"모델 정보 조회 실패: {e}")
            return {
                'model_name': self.model_name,
                'status': 'error',
                'error': str(e)
            }
    
    def validate_ollama_connection(self) -> bool:
        """
        Ollama 서버 연결 확인
        
        Returns:
            연결 성공 여부
        """
        try:
            ollama.list()
            logger.info("Ollama 서버 연결 성공")
            return True
        except Exception as e:
            logger.error(f"Ollama 서버 연결 실패: {e}")
            return False


# 단독 함수 인터페이스 (기존 CLI 호환성)
def analyze_bladder_question(question: str, model_name: str = "gemma3:4b") -> str:
    """
    방광암 질문 분석 함수 (단순 인터페이스)
    
    Args:
        question: 분석할 의료 질문
        model_name: 사용할 Ollama 모델
        
    Returns:
        의료 전문 응답
    """
    analyzer = BladderAnalyzer(model_name=model_name)
    return analyzer.analyze_bladder_question(question)


# 테스트용 코드
if __name__ == "__main__":
    # 간단한 테스트
    test_question = "What are the main treatment options for bladder cancer?"
    analyzer = BladderAnalyzer()
    
    # 연결 확인
    if analyzer.validate_ollama_connection():
        print("✓ Ollama 서버 연결됨")
        print(f"모델 정보: {analyzer.get_model_info()}")
        
        # 테스트 질문
        response = analyzer.analyze_bladder_question(test_question)
        print(f"\n질문: {test_question}")
        print(f"응답:\n{response}")
    else:
        print("✗ Ollama 서버 연결 실패")