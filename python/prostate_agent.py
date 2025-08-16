#!/usr/bin/env python3
"""
DR-Prostate-CLI Agent
전립선 질환 EAU 가이드라인 AI Agent - Ollama + RAG 기반
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
import ollama

class ProstateAgent:
    """전립선 질환 전문 AI 에이전트"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.llm = None
        self.embeddings = None
        self.vector_store = None
        self.chroma_client = None
        self.collection = None
        
        # 문서 경로 설정
        self.pdf_path = Path(__file__).parent / "files" / "EAU-EANM-ESTRO-ESUR-ISUP-SIOG-Guidelines-on-Prostate-Cancer-2025_updated.pdf"
        if not self.pdf_path.exists():
            # 상위 디렉토리에서 찾기
            self.pdf_path = Path(__file__).parent.parent / "files" / "EAU-EANM-ESTRO-ESUR-ISUP-SIOG-Guidelines-on-Prostate-Cancer-2025_updated.pdf"
        
        # ChromaDB 설정
        self.chroma_db_path = Path(__file__).parent.parent / "chroma_db_prostate"
        
    def initialize(self) -> bool:
        """에이전트 초기화"""
        try:
            self.logger.info("전립선 에이전트 초기화 시작...")
            
            # Ollama 연결 확인
            if not self._check_ollama_connection():
                self.logger.error("Ollama 서버에 연결할 수 없습니다")
                return False
            
            # LLM 초기화
            self.llm = OllamaLLM(
                model=self.config.model_name,
                temperature=0.1,
                num_ctx=4096
            )
            
            # 임베딩 초기화
            self.embeddings = OllamaEmbeddings(
                model="mxbai-embed-large",
                base_url="http://localhost:11434"
            )
            
            # ChromaDB 초기화
            if not self._setup_vector_database():
                self.logger.error("벡터 데이터베이스 설정 실패")
                return False
            
            self.logger.info("전립선 에이전트 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"에이전트 초기화 실패: {str(e)}")
            return False
    
    def _check_ollama_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            models = ollama.list()
            
            # 필요한 모델들이 있는지 확인
            model_names = [model['name'] for model in models.get('models', [])]
            
            required_models = [self.config.model_name, "mxbai-embed-large"]
            missing_models = [model for model in required_models if not any(model in name for name in model_names)]
            
            if missing_models:
                self.logger.warning(f"누락된 모델: {missing_models}")
                # 자동으로 다운로드 시도
                for model in missing_models:
                    try:
                        self.logger.info(f"모델 {model} 다운로드 중...")
                        ollama.pull(model)
                        self.logger.info(f"모델 {model} 다운로드 완료")
                    except Exception as e:
                        self.logger.error(f"모델 {model} 다운로드 실패: {str(e)}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ollama 연결 확인 실패: {str(e)}")
            return False
    
    def _setup_vector_database(self) -> bool:
        """벡터 데이터베이스 설정"""
        try:
            # ChromaDB 클라이언트 초기화
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 컬렉션 가져오기 또는 생성
            collection_name = "prostate_guidelines"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                self.logger.info("기존 전립선 가이드라인 컬렉션 로드됨")
                
                # 컬렉션이 비어있는지 확인
                if self.collection.count() == 0:
                    self.logger.info("컬렉션이 비어있어 PDF 문서를 다시 처리합니다")
                    return self._process_pdf_documents()
                    
            except Exception:
                # 컬렉션이 없으면 새로 생성
                self.logger.info("새로운 전립선 가이드라인 컬렉션 생성")
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "EAU Prostate Cancer Guidelines 2025"}
                )
                return self._process_pdf_documents()
            
            return True
            
        except Exception as e:
            self.logger.error(f"벡터 데이터베이스 설정 실패: {str(e)}")
            return False
    
    def _process_pdf_documents(self) -> bool:
        """PDF 문서 처리 및 벡터화"""
        try:
            if not self.pdf_path.exists():
                self.logger.error(f"PDF 파일을 찾을 수 없습니다: {self.pdf_path}")
                return False
            
            self.logger.info(f"PDF 문서 처리 중: {self.pdf_path}")
            
            # PDF 로드
            loader = PyPDFLoader(str(self.pdf_path))
            documents = loader.load()
            
            self.logger.info(f"PDF에서 {len(documents)} 페이지 로드됨")
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            texts = text_splitter.split_documents(documents)
            self.logger.info(f"{len(texts)} 개의 텍스트 청크 생성됨")
            
            # 배치 처리로 임베딩 생성 및 저장
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # 텍스트와 메타데이터 준비
                batch_texts = [doc.page_content for doc in batch]
                batch_metadatas = [doc.metadata for doc in batch]
                batch_ids = [f"prostate_doc_{i + j}" for j in range(len(batch))]
                
                # 임베딩 생성
                self.logger.info(f"배치 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} 임베딩 생성 중...")
                batch_embeddings = self.embeddings.embed_documents(batch_texts)
                
                # ChromaDB에 추가
                self.collection.add(
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
            
            self.logger.info("PDF 문서 처리 및 벡터화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 문서 처리 실패: {str(e)}")
            return False
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """질문에 대한 답변 생성"""
        try:
            self.logger.info(f"질문 처리 중: {question[:100]}...")
            
            # 질문을 벡터화하여 관련 문서 검색
            question_embedding = self.embeddings.embed_query(question)
            
            # 유사한 문서 검색
            search_results = self.collection.query(
                query_embeddings=[question_embedding],
                n_results=5,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 검색된 문서들을 컨텍스트로 구성
            context_docs = []
            if search_results['documents'] and search_results['documents'][0]:
                for i, doc in enumerate(search_results['documents'][0]):
                    metadata = search_results['metadatas'][0][i] if search_results['metadatas'][0] else {}
                    distance = search_results['distances'][0][i] if search_results['distances'][0] else 0
                    
                    context_docs.append({
                        'content': doc,
                        'page': metadata.get('page', 'Unknown'),
                        'source': metadata.get('source', 'Unknown'),
                        'relevance': 1 - distance  # 거리를 관련성으로 변환
                    })
            
            # 컨텍스트 텍스트 구성
            context_text = "\n\n".join([f"[Page {doc['page']}] {doc['content']}" for doc in context_docs])
            
            # 프롬프트 구성
            prompt = f"""
당신은 전립선 질환 전문 AI 의사입니다. EAU (European Association of Urology) 전립선암 가이드라인 2025를 기반으로 정확하고 전문적인 의료 정보를 제공합니다.

**참고 문서:**
{context_text}

**환자 질문:**
{question}

**응답 지침:**
1. EAU 가이드라인 2025를 우선적으로 참조하여 답변하세요
2. 전립선암, 전립선비대증, 전립선염 등 전립선 관련 질환에 집중하세요
3. 의학적으로 정확하고 근거 기반의 정보를 제공하세요
4. 환자가 이해하기 쉽게 설명하되, 전문성을 유지하세요
5. 진단, 치료, 관리 방법에 대해 체계적으로 설명하세요
6. 필요시 PSA 검사, 생검, 영상검사 등의 정보를 포함하세요
7. 반드시 전문 의료진과의 상담 필요성을 강조하세요

**응답 형식:**
🏥 **의료 정보**

[구체적이고 체계적인 답변]

**Disclaimer:** 저는 DR_PROSTATE로서 의료 자문을 제공하지만, 이는 전문적인 의학적 조언이 아닙니다. 반드시 urologists (전립선 전문의) 및 oncologists (종양 전문의)와 상담하여 개인에게 맞는 진단 및 치료 계획을 결정하십시오.

⚠️ **의학적 주의사항**: 이 정보는 교육 목적으로만 제공됩니다. 실제 진단과 치료는 반드시 전문 의료진과 상담하시기 바랍니다.
"""
            
            # LLM을 사용해 답변 생성
            response = self.llm.invoke(prompt)
            
            self.logger.info("답변 생성 완료")
            
            return {
                'success': True,
                'answer': response,
                'sources': context_docs,
                'question': question
            }
            
        except Exception as e:
            self.logger.error(f"질문 처리 실패: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def get_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보 반환"""
        try:
            status = {
                'ollama_connected': False,
                'model_available': False,
                'pdf_loaded': False,
                'vectordb_ready': False
            }
            
            # Ollama 연결 확인
            try:
                models = ollama.list()
                status['ollama_connected'] = True
                
                # 모델 가용성 확인
                model_names = [model['name'] for model in models.get('models', [])]
                status['model_available'] = any(self.config.model_name in name for name in model_names)
                
            except:
                pass
            
            # PDF 파일 확인
            status['pdf_loaded'] = self.pdf_path.exists()
            
            # 벡터 데이터베이스 확인
            try:
                if self.collection:
                    status['vectordb_ready'] = self.collection.count() > 0
            except:
                pass
            
            return status
            
        except Exception as e:
            self.logger.error(f"상태 확인 실패: {str(e)}")
            return {
                'ollama_connected': False,
                'model_available': False,
                'pdf_loaded': False,
                'vectordb_ready': False,
                'error': str(e)
            }