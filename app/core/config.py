import os

# ==========================================================
# Database Configuration
# ==========================================================
# DB 접속 정보를 환경 변수에서 읽어옵니다.
# - 운영 환경에서는 .env / Docker / Kubernetes Secret 등으로 주입됩니다.
# - 로컬 개발 환경을 위해 기본값을 설정합니다.
# - 환경 변수가 없을 경우 기본값(localhost, root 등)을 사용합니다.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")

# ==========================================================
# Ollama LLM Configuration
# ==========================================================
# 로컬 Ollama 서버 API endpoint 및 사용할 모델 설정
# - OLLAMA_URL: Ollama API generate endpoint
# - OLLAMA_MODEL: 사용할 LLM 모델 이름
#
# 운영 환경에서는 모델을 환경 변수로 관리하여
# 코드 수정 없이 모델 교체가 가능하도록 합니다.
# 기본값은 llama3.2 모델을 사용합니다.
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")