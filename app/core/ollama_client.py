import requests
from app.core.config import OLLAMA_URL, OLLAMA_MODEL


def call_ollama(prompt: str) -> str:
    """
    Ollama LLM 서버에 프롬프트를 전달하고 생성된 응답을 반환하는 함수

    - 내부 Ollama API(generate endpoint)를 호출하여 LLM 응답을 생성합니다.
    - 스트리밍 모드는 사용하지 않고 단일 응답(JSON)을 반환받습니다.
    - 네트워크 오류, HTTP 오류, 응답 형식 오류에 대한 예외 처리를 수행합니다.

    Args:
        prompt (str): LLM에 전달할 프롬프트 문자열

    Returns:
        str: LLM이 생성한 텍스트 응답

    Raises:
        ValueError: 프롬프트가 비어 있거나 응답 형식이 잘못된 경우
        RuntimeError: Ollama API 호출 또는 처리 과정에서 오류가 발생한 경우
    """

    # --------------------------------------------------
    # 1. 입력값 검증
    # --------------------------------------------------
    # 빈 문자열 또는 공백만 있는 프롬프트는 LLM 호출을 하지 않도록 차단
    if not prompt or not prompt.strip():
        raise ValueError("프롬프트가 비어 있습니다.")

    try:
        # --------------------------------------------------
        # 2. Ollama API 요청
        # --------------------------------------------------
        # generate API에 JSON payload로 model / prompt 전달
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,  # 사용할 LLM 모델 이름
                "prompt": prompt,       # LLM 입력 프롬프트
                "stream": False,        # 스트리밍 비활성화 (단일 응답)
            },
            timeout=120,               # LLM 응답 지연 대비 timeout 설정
        )

        # HTTP 오류(4xx, 5xx) 발생 시 예외 발생
        r.raise_for_status()

        # --------------------------------------------------
        # 3. 응답 파싱
        # --------------------------------------------------
        data = r.json()

        # Ollama generate API 기본 응답 필드
        # ex) {"response": "..."}
        response_text = data.get("response", "")

        # 응답 타입 검증
        if not isinstance(response_text, str):
            raise ValueError("Ollama 응답의 'response'가 문자열이 아닙니다.")

        return response_text.strip()

    # --------------------------------------------------
    # 4. 네트워크 오류 처리
    # --------------------------------------------------
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {str(e)}") from e

    # --------------------------------------------------
    # 5. 입력 / 응답 검증 오류
    # --------------------------------------------------
    except ValueError:
        raise

    # --------------------------------------------------
    # 6. 기타 예외 처리
    # --------------------------------------------------
    except Exception as e:
        raise RuntimeError(f"Ollama 처리 중 오류: {str(e)}") from e