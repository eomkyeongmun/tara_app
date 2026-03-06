import os
import re
import difflib
from urllib.parse import unquote_plus

import mysql.connector
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# FastAPI 인스턴스 생성
app = FastAPI()

# ==========================================================
# 1. 환경 변수 설정 (Environment Variables)
#    - docker-compose.yml에 설정된 값을 우선적으로 가져옵니다.
#    - 값이 없을 경우를 대비해 기본값(Default)을 설정해두었습니다.
# ==========================================================
DB_HOST = os.getenv("DB_HOST", "localhost")       # 도커 네트워크 내부의 서비스 이름인 "db"로 연결됨
DB_USER = os.getenv("DB_USER", "root")            # MySQL 접속 아이디
DB_PASSWORD = os.getenv("DB_PASSWORD", "")        # MySQL 접속 비밀번호
DB_NAME = os.getenv("DB_NAME", "")                # 사용할 데이터베이스 이름

# Ollama API 엔드포인트 및 모델 설정
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinydolphin:latest")

# MySQL 연결을 위한 딕셔너리 구성
db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
}

# ==========================================================
# 2. 데이터 스키마 (Pydantic Models)
#    - 클라이언트로부터 받을 JSON 데이터의 형식을 정의합니다.
#    - 데이터 검증(Validation)이 자동으로 수행됩니다.
# ==========================================================
class LoginRequest(BaseModel):
    username: str
    password: str

# ==========================================================
# 3. 데이터베이스 헬퍼 (DB Helper)
#    - 필요할 때마다 새로운 DB 연결 객체를 생성하여 반환합니다.
# ==========================================================
def get_db_conn():
    return mysql.connector.connect(**db_config)

# ==========================================================
# 4. 엔드포인트 (Routes)
# ==========================================================

@app.get("/")
def health():
    """
    [서버 상태 확인]
    - 컨테이너가 정상적으로 실행 중인지, 환경 변수가 잘 주입되었는지 확인하는 용도입니다.
    """
    return {
        "ok": True,
        "db_host": DB_HOST,
        "db_name": DB_NAME,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
    }

@app.post("/login")
def login(data: LoginRequest):
    """
    [로그인 API]
    - 사용자가 보낸 ID/PW를 DB의 users 테이블과 대조합니다.
    - 로그인 성공 시 'login_logs' 테이블에 이력을 남깁니다.
    """
    username = data.username
    password = data.password

    conn = None
    cursor = None

    try:
        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True) # 결과값을 딕셔너리 형태로 받음

        # 1. 사용자 일치 확인 (SQL Injection 방지를 위해 바인딩 변수 %s 사용)
        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        if result:
            print(f"[LOGIN SUCCESS] {username}")

            # 2. 로그인 성공 시 로그 기록 저장
            try:
                cursor.execute(
                    "INSERT INTO login_logs (username) VALUES (%s)",
                    (username,),
                )
                conn.commit() # INSERT 작업 후 반드시 commit 필요
            except Exception as e:
                print(f"[LOG ERROR] {e}") # 로그 기록 실패 시 에러 출력 (메인 로직에 영향 X)

            return {"success": True, "message": "Login successful"}

        # 3. 일치하는 정보가 없을 경우
        return {"success": False, "message": "Invalid credentials"}

    except mysql.connector.Error as e:
        # DB 연결 자체가 안되거나 쿼리 에러 발생 시 500 에러 반환
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
    finally:
        # DB 자원 반납 (에러 여부와 관계없이 실행)
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/analyze")
def analyze(text: str = ""):
    """
    [AI 분석 API]
    - 텍스트를 입력받아 Ollama AI에게 전달하고, 받은 답변을 정규화하여 반환합니다.
    """
    # URL 인코딩된 텍스트를 디코딩 (예: %20 -> 공백)
    prompt = unquote_plus(text or "")

    try:
        # 1. Ollama 서버에 POST 요청
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False, # 실시간 스트리밍이 아닌 한 번에 결과 받기
            },
            timeout=120, # AI 처리가 길어질 수 있으므로 충분한 타임아웃 설정
        )
        r.raise_for_status() # HTTP 응답 코드가 200이 아니면 예외 발생

        result = r.json().get("response", "No Response")

        # 2. 프롬프트 내에 제시된 '선택지(Options)' 추출 및 결과 매칭
        options = extract_options_from_prompt(prompt)
        normalized = normalize_response(result, options)

        # AI 원본 답변과 정규화된 답변(예: A, B, C 중 하나)을 같이 반환
        return {"response": result, "normalized": normalized}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ==========================================================
# 5. 유틸리티 함수 (Helpers)
# ==========================================================

def extract_options_from_prompt(prompt_text: str):
    """
    [프롬프트 분석]
    - 프롬프트 텍스트 중에서 'Options (choose one):' 아래 줄에 있는 선택지들을 추출합니다.
    - 예: "Options (choose one):\n Yes, No" -> ['Yes', 'No'] 추출
    """
    match = re.search(r"Options \(choose one\):\s*\n([^\n]+)", prompt_text)
    if not match:
        return []

    raw_line = match.group(1).strip()
    # 쉼표로 구분된 단어들을 리스트로 변환하고 양쪽 공백 제거
    return [opt.strip() for opt in raw_line.split(",") if opt.strip()]

def normalize_response(raw_response: str, options: list[str]) -> str:
    """
    [AI 답변 정규화]
    - AI가 수다스러울 경우(예: "제 생각엔 Yes인 것 같습니다") 선택지 중 하나로 변환합니다.
    1. 대소문자 무시하고 정확히 일치하는지 확인
    2. 답변 내용 중에 선택지 단어가 포함되어 있는지 확인
    3. 오타가 있을 경우 가장 유사한 단어 추천 (difflib 활용)
    """
    raw = (raw_response or "").lower().strip()
    options_lower = [opt.lower() for opt in options]

    # 1) 완전 일치 확인
    for i, opt in enumerate(options_lower):
        if raw == opt:
            return options[i]

    # 2) 답변 안에 선택지 키워드가 들어있는지 확인
    for i, opt in enumerate(options_lower):
        if opt and opt in raw:
            return options[i]

    # 3) 유사도 매칭 (가장 비슷한 단어 찾기, 정확도 50% 이상)
    best_match = difflib.get_close_matches(raw, options_lower, n=1, cutoff=0.5)
    if best_match:
        idx = options_lower.index(best_match[0])
        return options[idx]

    # 매칭되는 게 전혀 없다면 "Unknown" 반환
    return "Unknown"