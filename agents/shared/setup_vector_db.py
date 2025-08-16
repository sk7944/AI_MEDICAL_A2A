"""
의료 가이드라인 PDF를 벡터 DB로 구축하는 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.shared.vector_db import MedicalVectorDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_medical_vector_db():
    """의료 가이드라인 벡터 DB 구축"""
    
    # 벡터 DB 초기화
    db = MedicalVectorDB(
        db_path="./chroma_db",
        collection_name="medical_guidelines"
    )
    
    # 가이드라인 PDF 경로
    guidelines = [
        {
            "path": "./files/EAU-EANM-ESTRO-ESUR-ISUP-SIOG-Guidelines-on-Prostate-Cancer-2025_updated.pdf",
            "source_type": "prostate",
            "name": "EAU Prostate Cancer Guidelines 2025"
        },
        {
            "path": "./files/EAU-Guidelines-on-Non-muscle-invasive-Bladder-Cancer-2025.pdf",
            "source_type": "bladder",
            "name": "EAU Non-muscle-invasive Bladder Cancer Guidelines 2025"
        }
    ]
    
    # 각 가이드라인 처리
    for guideline in guidelines:
        pdf_path = guideline["path"]
        
        if not os.path.exists(pdf_path):
            logger.warning(f"PDF not found: {pdf_path}")
            continue
        
        logger.info(f"Processing: {guideline['name']}")
        
        # PDF 처리 및 벡터 DB 저장
        result = db.process_pdf(
            pdf_path=pdf_path,
            source_type=guideline["source_type"],
            chunk_size=1000,
            chunk_overlap=200
        )
        
        if result["status"] == "success":
            logger.info(f"✓ Successfully processed {guideline['name']}")
            logger.info(f"  - Chunks created: {result['chunks_processed']}")
        else:
            logger.error(f"✗ Failed to process {guideline['name']}: {result.get('error')}")
    
    # 최종 통계
    stats = db.get_stats()
    logger.info("\n=== Vector DB Statistics ===")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info(f"Source types: {stats.get('source_types', {})}")
    logger.info(f"DB path: {stats['db_path']}")
    
    # 테스트 검색
    logger.info("\n=== Test Search ===")
    test_queries = [
        ("PSA testing guidelines", "prostate"),
        ("BCG treatment", "bladder"),
        ("Gleason score", "prostate")
    ]
    
    for query, source_type in test_queries:
        results = db.search(query, source_type=source_type, n_results=2)
        logger.info(f"Query: '{query}' ({source_type}) - Found {len(results)} results")
        if results:
            logger.info(f"  Top result preview: {results[0]['text'][:100]}...")


if __name__ == "__main__":
    setup_medical_vector_db()