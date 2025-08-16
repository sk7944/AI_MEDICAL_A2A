"""
Vector Database Management using ChromaDB
의료 가이드라인 PDF 처리 및 검색 시스템
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalVectorDB:
    """의료 가이드라인 벡터 데이터베이스 관리"""
    
    def __init__(self, 
                 db_path: str = "./chroma_db",
                 collection_name: str = "medical_guidelines",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        초기화
        
        Args:
            db_path: ChromaDB 저장 경로
            collection_name: 컬렉션 이름
            embedding_model: 임베딩 모델 이름
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # 디렉토리 생성
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 임베딩 모델 초기화
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        
        # 임베딩 함수 정의
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # 컬렉션 가져오거나 생성
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def process_pdf(self, 
                   pdf_path: str, 
                   source_type: str,
                   chunk_size: int = 1000,
                   chunk_overlap: int = 200) -> Dict[str, Any]:
        """
        PDF 파일 처리 및 벡터 DB 저장
        
        Args:
            pdf_path: PDF 파일 경로
            source_type: 소스 타입 (bladder, prostate 등)
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩
            
        Returns:
            처리 결과 정보
        """
        try:
            # PDF 파일 체크
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            logger.info(f"Processing PDF: {pdf_path}")
            
            # PDF 로드
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            
            chunks = text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from PDF")
            
            # 각 청크에 메타데이터 추가
            texts = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # 텍스트 추출
                text = chunk.page_content
                texts.append(text)
                
                # 메타데이터 생성
                metadata = {
                    "source": pdf_path,
                    "source_type": source_type,
                    "page": chunk.metadata.get("page", 0),
                    "chunk_index": i,
                    "chunk_size": len(text)
                }
                metadatas.append(metadata)
                
                # 고유 ID 생성
                chunk_id = f"{source_type}_{i}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
                ids.append(chunk_id)
            
            # ChromaDB에 추가
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector DB")
            
            return {
                "status": "success",
                "pdf_path": pdf_path,
                "chunks_processed": len(chunks),
                "source_type": source_type
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def search(self, 
              query: str, 
              source_type: Optional[str] = None,
              n_results: int = 5) -> List[Dict[str, Any]]:
        """
        벡터 검색 수행
        
        Args:
            query: 검색 쿼리
            source_type: 특정 소스 타입으로 필터링 (옵션)
            n_results: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 필터 생성
            where_filter = {}
            if source_type:
                where_filter = {"source_type": source_type}
            
            # 검색 수행
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0,
                        "id": results['ids'][0][i] if results['ids'] else ""
                    })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def get_context_for_prompt(self, 
                               query: str, 
                               source_type: Optional[str] = None,
                               n_results: int = 3) -> str:
        """
        프롬프트에 사용할 컨텍스트 생성
        
        Args:
            query: 검색 쿼리
            source_type: 소스 타입
            n_results: 사용할 결과 수
            
        Returns:
            컨텍스트 텍스트
        """
        results = self.search(query, source_type, n_results)
        
        if not results:
            return ""
        
        # 컨텍스트 구성
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result['metadata'].get('source', 'Unknown')
            page = result['metadata'].get('page', 'N/A')
            text = result['text']
            
            context_parts.append(
                f"[Reference {i} - Page {page}]:\n{text}\n"
            )
        
        context = "\n---\n".join(context_parts)
        return f"Based on the following medical guidelines:\n\n{context}"
    
    def get_stats(self) -> Dict[str, Any]:
        """
        데이터베이스 통계 반환
        
        Returns:
            통계 정보
        """
        try:
            count = self.collection.count()
            
            # 소스 타입별 카운트 (간단한 방법)
            all_data = self.collection.get()
            source_types = {}
            
            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    src_type = metadata.get('source_type', 'unknown')
                    source_types[src_type] = source_types.get(src_type, 0) + 1
            
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name,
                "source_types": source_types,
                "db_path": str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self, source_type: Optional[str] = None):
        """
        컬렉션 클리어
        
        Args:
            source_type: 특정 소스 타입만 삭제 (옵션)
        """
        try:
            if source_type:
                # 특정 소스 타입만 삭제
                results = self.collection.get(
                    where={"source_type": source_type}
                )
                if results['ids']:
                    self.collection.delete(ids=results['ids'])
                    logger.info(f"Cleared {len(results['ids'])} documents of type {source_type}")
            else:
                # 전체 컬렉션 삭제 및 재생성
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self._embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("Cleared entire collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")


# 싱글톤 인스턴스
_vector_db_instance = None

def get_vector_db(db_path: str = "./chroma_db") -> MedicalVectorDB:
    """벡터 DB 싱글톤 인스턴스 반환"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = MedicalVectorDB(db_path=db_path)
    return _vector_db_instance


if __name__ == "__main__":
    # 테스트 코드
    db = MedicalVectorDB()
    
    # 통계 출력
    stats = db.get_stats()
    print(f"Database stats: {stats}")
    
    # 테스트 검색
    test_results = db.search("PSA testing", n_results=2)
    print(f"Test search results: {len(test_results)} found")