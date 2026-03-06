# Python 3.11 기반 공식 이미지 사용
# - FastAPI 애플리케이션 실행을 위한 런타임 환경 제공
FROM python:3.11

# 컨테이너 내부 작업 디렉토리 설정
# 이후 모든 명령(COPY, RUN 등)은 /app 기준으로 실행
WORKDIR /app

# Python 의존성 목록 먼저 복사
# - Docker layer 캐시를 활용하기 위해 requirements.txt만 먼저 복사
COPY requirements.txt .

# 의존성 패키지 설치
# - requirements.txt에 정의된 라이브러리 설치
RUN pip install -r requirements.txt

# 애플리케이션 전체 소스 코드 복사
# - 현재 프로젝트 디렉토리의 모든 파일을 컨테이너 /app에 복사
COPY . .

# Python 모듈 import 경로 설정
# - app 패키지를 루트 모듈로 인식하도록 설정
ENV PYTHONPATH=/app

# 컨테이너 실행 시 FastAPI 서버 시작
# - uvicorn ASGI 서버로 app.main의 FastAPI 인스턴스를 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]