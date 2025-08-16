"""
Medical Consultation Orchestrator
두 전문 AI 에이전트(DR_BLADDER, DR_PROSTATE)에게 질의하고 결과를 종합하는 오케스트레이터
"""

import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime
import ollama

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalOrchestrator:
    """의료 상담 오케스트레이터 클래스"""
    
    def __init__(self):
        self.bladder_api_url = "http://localhost:8001"
        self.prostate_api_url = "http://localhost:8002"
        self.model_name = "gemma3:4b"
        
        # Ollama 연결 테스트
        self.validate_ollama_connection()
    
    def validate_ollama_connection(self) -> bool:
        """Ollama 연결 상태 확인"""
        try:
            ollama.list()
            logger.info("✅ Ollama 연결 성공")
            return True
        except Exception as e:
            logger.error(f"❌ Ollama 연결 실패: {e}")
            return False
    
    def check_agent_health(self, agent_name: str, url: str) -> Dict[str, Any]:
        """개별 에이전트 헬스체크"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ {agent_name} 상태: {health_data.get('status', 'unknown')}")
                return {"status": "healthy", "data": health_data}
            else:
                logger.warning(f"⚠️ {agent_name} 응답 코드: {response.status_code}")
                return {"status": "degraded", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ {agent_name} 헬스체크 실패: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_all_agents_health(self) -> Dict[str, Any]:
        """모든 에이전트 헬스체크"""
        return {
            "bladder": self.check_agent_health("DR_BLADDER", self.bladder_api_url),
            "prostate": self.check_agent_health("DR_PROSTATE", self.prostate_api_url),
            "orchestrator": {"status": "healthy", "model": self.model_name}
        }
    
    async def query_agent_async(self, session: aiohttp.ClientSession, agent_name: str, 
                               url: str, question: str) -> Dict[str, Any]:
        """비동기로 개별 에이전트에게 질의"""
        try:
            logger.info(f"🔄 {agent_name}에게 질의 중...")
            
            async with session.post(
                f"{url}/ask",
                json={"question": question},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ {agent_name} 응답 완료")
                    return {
                        "agent": agent_name,
                        "status": "success",
                        "response": result,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ {agent_name} 응답 실패: {response.status}")
                    return {
                        "agent": agent_name,
                        "status": "error",
                        "error": f"HTTP {response.status}: {error_text}",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"❌ {agent_name} 질의 실패: {e}")
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def query_all_agents(self, question: str) -> Dict[str, Any]:
        """모든 에이전트에게 동시에 질의"""
        logger.info(f"🚀 의료 상담 시작: {question[:100]}...")
        
        async with aiohttp.ClientSession() as session:
            # 두 에이전트에게 동시에 질의
            tasks = [
                self.query_agent_async(session, "DR_BLADDER", self.bladder_api_url, question),
                self.query_agent_async(session, "DR_PROSTATE", self.prostate_api_url, question)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            bladder_result = results[0] if not isinstance(results[0], Exception) else {
                "agent": "DR_BLADDER", "status": "error", "error": str(results[0])
            }
            prostate_result = results[1] if not isinstance(results[1], Exception) else {
                "agent": "DR_PROSTATE", "status": "error", "error": str(results[1])
            }
            
            return {
                "question": question,
                "bladder_consultation": bladder_result,
                "prostate_consultation": prostate_result,
                "query_timestamp": datetime.now().isoformat()
            }
    
    def synthesize_consultation(self, consultation_data: Dict[str, Any]) -> Dict[str, Any]:
        """두 전문가 의견을 종합하여 최종 의료 상담 결과 생성"""
        try:
            logger.info("🧠 의료 상담 결과 종합 중...")
            
            question = consultation_data["question"]
            bladder_result = consultation_data["bladder_consultation"]
            prostate_result = consultation_data["prostate_consultation"]
            
            # 각 전문가 의견 추출
            bladder_opinion = ""
            prostate_opinion = ""
            
            if bladder_result["status"] == "success":
                bladder_opinion = bladder_result["response"].get("answer", "응답 없음")
            else:
                bladder_opinion = f"오류: {bladder_result.get('error', '알 수 없는 오류')}"
            
            if prostate_result["status"] == "success":
                prostate_opinion = prostate_result["response"].get("answer", "응답 없음")
            else:
                prostate_opinion = f"오류: {prostate_result.get('error', '알 수 없는 오류')}"
            
            # 종합 의견 생성을 위한 프롬프트
            synthesis_prompt = f"""
당신은 의료 상담 결과를 종합하는 전문 의료 AI입니다. 
두 전문가의 의견을 바탕으로 환자에게 도움이 되는 종합적인 의료 정보를 제공해주세요.

**환자 질문:**
{question}

**방광 전문가 (DR_BLADDER) 의견:**
{bladder_opinion}

**전립선 전문가 (DR_PROSTATE) 의견:**
{prostate_opinion}

**요청사항:**
1. 두 전문가 의견을 종합하여 환자에게 도움이 되는 통합된 답변을 제공해주세요
2. 각 전문가의 핵심 포인트를 정리해주세요
3. 추가적으로 고려해야 할 사항이 있다면 언급해주세요
4. 반드시 전문 의료진과의 상담 필요성을 강조해주세요

**형식:**
📋 **종합 의료 상담 결과**

## 핵심 요약
[두 전문가 의견의 핵심 내용]

## 방광 전문가 주요 의견
[DR_BLADDER의 핵심 포인트]

## 전립선 전문가 주요 의견  
[DR_PROSTATE의 핵심 포인트]

## 통합 권장사항
[종합적인 권장사항]

## 추가 고려사항
[추가로 고려해야 할 내용]

⚠️ **중요한 의학적 면책조항**: 이 정보는 교육 목적으로만 제공됩니다. 실제 진단과 치료는 반드시 전문 의료진과 상담하시기 바랍니다.
"""
            
            # Ollama를 사용한 종합 의견 생성
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {
                            'role': 'user',
                            'content': synthesis_prompt
                        }
                    ]
                )
                synthesis = response['message']['content']
                logger.info("✅ 의료 상담 결과 종합 완료")
            except Exception as e:
                logger.error(f"❌ 종합 의견 생성 실패: {e}")
                synthesis = f"종합 의견 생성에 실패했습니다. 각 전문가 의견을 개별적으로 참고해주세요.\n\n오류: {str(e)}"
            
            return {
                "question": question,
                "individual_consultations": {
                    "bladder_specialist": bladder_result,
                    "prostate_specialist": prostate_result
                },
                "synthesized_consultation": synthesis,
                "consultation_timestamp": datetime.now().isoformat(),
                "orchestrator_info": {
                    "version": "1.0.0",
                    "model": self.model_name,
                    "synthesis_status": "success" if "종합 의견 생성에 실패" not in synthesis else "partial"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 상담 결과 종합 실패: {e}")
            return {
                "question": consultation_data.get("question", "알 수 없음"),
                "error": f"상담 결과 종합 중 오류 발생: {str(e)}",
                "individual_consultations": consultation_data,
                "consultation_timestamp": datetime.now().isoformat(),
                "orchestrator_info": {
                    "version": "1.0.0",
                    "model": self.model_name,
                    "synthesis_status": "error"
                }
            }
    
    async def full_consultation(self, question: str) -> Dict[str, Any]:
        """전체 의료 상담 프로세스 실행"""
        try:
            # 1. 모든 에이전트에게 질의
            consultation_data = await self.query_all_agents(question)
            
            # 2. 결과 종합
            final_result = self.synthesize_consultation(consultation_data)
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 전체 상담 프로세스 실패: {e}")
            return {
                "question": question,
                "error": f"상담 프로세스 중 오류 발생: {str(e)}",
                "consultation_timestamp": datetime.now().isoformat(),
                "orchestrator_info": {
                    "version": "1.0.0",
                    "model": self.model_name,
                    "synthesis_status": "error"
                }
            }


# 메인 함수 (테스트용)
async def main():
    """테스트용 메인 함수"""
    orchestrator = MedicalOrchestrator()
    
    # 헬스체크
    health = orchestrator.check_all_agents_health()
    print("🏥 시스템 상태:")
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    # 테스트 질문
    test_question = "소변에 피가 보이고 자주 소변을 봅니다. 어떤 검사를 받아야 하나요?"
    
    print(f"\n❓ 테스트 질문: {test_question}")
    print("=" * 80)
    
    result = await orchestrator.full_consultation(test_question)
    print("\n📋 최종 상담 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())