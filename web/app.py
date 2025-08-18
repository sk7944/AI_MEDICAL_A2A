"""
AI Medical A2A Consultation Web Interface
Flask 기반 웹 애플리케이션
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import asyncio
import aiohttp
from datetime import datetime
import logging
import time
import markdown
import re

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flask_app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Flask 요청 로깅 활성화
@app.before_request
def log_request_info():
    logger.info(f"🌐 요청: {request.method} {request.url}")
    if request.method == 'POST':
        logger.info(f"📝 POST 데이터: {request.form}")

@app.after_request
def log_response_info(response):
    logger.info(f"📤 응답: {response.status_code} for {request.url}")
    return response
app.secret_key = 'medical_consultation_secret_key_2024'

# API 엔드포인트 설정
ORCHESTRATOR_API = "http://localhost:8003"
BLADDER_API = "http://localhost:8001"
PROSTATE_API = "http://localhost:8002"

@app.route('/')
def index():
    """메인 페이지"""
    try:
        logger.info("🏠 메인 페이지 요청")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ 메인 페이지 오류: {str(e)}")
        return f"메인 페이지 오류: {str(e)}", 500

@app.route('/health')
def health_check():
    """시스템 헬스체크 페이지"""
    try:
        # 오케스트레이터 헬스체크
        response = requests.get(f"{ORCHESTRATOR_API}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return render_template('health.html', health_data=health_data, status="success")
        else:
            return render_template('health.html', 
                                 health_data={"error": f"HTTP {response.status_code}"}, 
                                 status="error")
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return render_template('health.html', 
                             health_data={"error": str(e)}, 
                             status="error")

@app.route('/consult', methods=['GET', 'POST'])
def consultation():
    """의료 상담 페이지"""
    try:
        if request.method == 'GET':
            logger.info("💬 상담 페이지 GET 요청")
            return render_template('consultation.html')
        
        elif request.method == 'POST':
            logger.info("💬 상담 페이지 POST 요청 시작")
            
            question = request.form.get('question', '').strip()
            logger.info(f"📝 질문 내용: {question[:100]}...")
            
            if not question:
                logger.warning("⚠️ 빈 질문 요청")
                return render_template('consultation.html', 
                                     error="질문을 입력해주세요.")
            
            logger.info(f"🚀 오케스트레이터로 요청 전송: {ORCHESTRATOR_API}/consult")
            
            # 오케스트레이터에게 상담 요청
            response = requests.post(
                f"{ORCHESTRATOR_API}/consult",
                json={"question": question},
                headers={"Content-Type": "application/json"},
                timeout=60  # 1분 타임아웃
            )
            
            logger.info(f"📡 오케스트레이터 응답: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ 상담 결과 수신 성공")
                return render_template('result.html', 
                                     consultation_result=result, 
                                     status="success")
            else:
                error_msg = f"상담 요청 실패: HTTP {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return render_template('consultation.html', 
                                     error=error_msg)
                
    except requests.exceptions.Timeout:
        error_msg = "상담 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        logger.error(f"⏰ {error_msg}")
        return render_template('consultation.html', error=error_msg)
        
    except Exception as e:
        error_msg = f"상담 중 오류가 발생했습니다: {str(e)}"
        logger.error(f"💥 상담 페이지 오류: {error_msg}")
        return render_template('consultation.html', error=error_msg)

@app.route('/api/consult', methods=['POST'])
def api_consultation():
    """API 전용 상담 엔드포인트 (AJAX용)"""
    try:
        logger.info("🔧 API 상담 엔드포인트 호출됨")
        
        # JSON과 Form 데이터 모두 지원
        if request.is_json:
            data = request.get_json()
            question = data.get('question', '').strip() if data else ''
            logger.info(f"📋 JSON 데이터 수신: {question[:50]}...")
        else:
            question = request.form.get('question', '').strip()
            logger.info(f"📋 Form 데이터 수신: {question[:50]}...")
        
        if not question:
            logger.warning("⚠️ 빈 질문 API 요청")
            return jsonify({"error": "질문을 입력해주세요."}), 400
        
        logger.info(f"🚀 오케스트레이터로 API 요청 전송: {ORCHESTRATOR_API}/consult")
        
        # 오케스트레이터에게 상담 요청
        response = requests.post(
            f"{ORCHESTRATOR_API}/consult",
            json={"question": question},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        logger.info(f"📡 오케스트레이터 API 응답: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ API 상담 결과 수신 성공")
            return jsonify(result)
        else:
            error_msg = f"상담 요청 실패: HTTP {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return jsonify({"error": error_msg}), 500
            
    except requests.exceptions.Timeout:
        error_msg = "상담 요청 시간이 초과되었습니다."
        logger.error(f"⏰ API {error_msg}")
        return jsonify({"error": error_msg}), 504
    except Exception as e:
        error_msg = f"상담 중 오류 발생: {str(e)}"
        logger.error(f"💥 API 상담 실패: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/progress/<consultation_id>')
def get_progress(consultation_id):
    """상담 진행 상황 조회 API"""
    try:
        response = requests.get(f"{ORCHESTRATOR_API}/progress/{consultation_id}", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "진행 상황을 찾을 수 없습니다."}), 404
    except Exception as e:
        logger.error(f"진행 상황 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def api_health():
    """API 헬스체크"""
    try:
        response = requests.get(f"{ORCHESTRATOR_API}/health", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"HTTP {response.status_code}"}), 500
    except Exception as e:
        logger.error(f"API 헬스체크 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/result', methods=['GET', 'POST'])
def result():
    """상담 결과 페이지"""
    try:
        if request.method == 'POST':
            logger.info("📋 결과 페이지 POST 요청")
            consultation_result_str = request.form.get('consultation_result')
            
            if consultation_result_str:
                try:
                    consultation_result = json.loads(consultation_result_str)
                    logger.info("✅ POST로 상담 결과 수신 성공")
                    return render_template('result.html', 
                                         consultation_result=consultation_result, 
                                         status="success")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON 파싱 오류: {str(e)}")
                    return render_template('result.html', 
                                         consultation_result=None, 
                                         status="error", 
                                         message="결과 데이터 파싱 오류")
            else:
                logger.warning("⚠️ POST 요청에 상담 결과 없음")
        
        logger.info("📋 결과 페이지 GET 요청")
        # GET 요청이거나 POST에 데이터가 없는 경우
        return render_template('result.html', 
                             consultation_result=None, 
                             status="info", 
                             message="상담 결과를 찾을 수 없습니다. 새로운 상담을 진행해주세요.")
                             
    except Exception as e:
        logger.error(f"❌ 결과 페이지 오류: {str(e)}")
        return f"결과 페이지 오류: {str(e)}", 500

@app.route('/about')
def about():
    """소개 페이지"""
    return render_template('about.html')

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    logger.error(f"🔍 404 오류: {request.url} 페이지를 찾을 수 없음")
    return render_template('error.html', 
                         error_code=404, 
                         error_message="페이지를 찾을 수 없습니다."), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"💥 500 오류: 내부 서버 오류 - {str(error)}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message="내부 서버 오류가 발생했습니다."), 500

# 템플릿 필터
@app.template_filter('datetime')
def datetime_filter(timestamp):
    """날짜시간 포맷팅 필터"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp

@app.template_filter('truncate_words')
def truncate_words(text, max_words=50):
    """텍스트 단어 수 제한 필터"""
    words = text.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + '...'
    return text

@app.template_filter('markdown')
def markdown_filter(text):
    """마크다운을 HTML로 변환하는 필터"""
    if not text:
        return ''
    
    # 마크다운을 HTML로 변환
    md = markdown.Markdown(
        extensions=[
            'tables',           # 테이블 지원
            'fenced_code',      # 코드 블록 지원
            'nl2br',           # 줄바꿈을 <br>로 변환
            'sane_lists'       # 리스트 개선
        ]
    )
    
    # 이모지와 특수 문자 처리
    text = re.sub(r'📋|🏥|⚠️|💡|🔍|📊|🎯', lambda m: f'<span class="emoji">{m.group()}</span>', text)
    
    # 마크다운 변환 실행
    html_content = md.convert(text)
    
    return html_content

if __name__ == '__main__':
    print("🚀 AI Medical A2A Consultation Web Server 시작")
    print("📱 웹 인터페이스: http://localhost:8000")
    print("🏥 시스템 상태: http://localhost:8000/health")
    print("💬 의료 상담: http://localhost:8000/consult")
    print("📋 상담 결과: http://localhost:8000/result")
    
    # 등록된 라우트 확인
    print("\n🔧 등록된 라우트:")
    for rule in app.url_map.iter_rules():
        print(f"  • {rule.methods} {rule.rule}")
    
    # Waitress WSGI 서버 사용
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)