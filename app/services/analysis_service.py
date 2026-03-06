from app.core.ollama_client import call_ollama
from app.utils.text_normalizer import extract_options_from_prompt, normalize_response


def analyze_text(text: str):
    """
    텍스트 분석 서비스 로직

    - 입력 텍스트를 기반으로 LLM(Ollama)을 호출하여 응답을 생성합니다.
    - 프롬프트에서 선택 옵션을 추출하고, LLM 응답을 정규화(normalization)합니다.
    - 최종적으로 원본 응답과 정규화된 결과를 함께 반환합니다.

    Args:
        text (str): 분석할 입력 텍스트

    Returns:
        dict: 분석 결과
            {
                "success": bool,
                "response": str,      # LLM 원본 응답
                "normalized": Any     # 정규화된 응답 결과
            }

    Raises:
        ValueError: 입력 텍스트가 비어 있는 경우
    """

    # --------------------------------------------------
    # 1. 입력 텍스트 전처리
    # --------------------------------------------------
    # None 또는 공백 입력을 방지하기 위해 문자열 정리
    prompt = (text or "").strip()

    if not prompt:
        raise ValueError("text is required")

    # --------------------------------------------------
    # 2. LLM(Ollama) 호출
    # --------------------------------------------------
    # 프롬프트를 Ollama API로 전달하여 응답 생성
    result = call_ollama(prompt)

    # --------------------------------------------------
    # 3. 프롬프트에서 선택 옵션 추출
    # --------------------------------------------------
    # 프롬프트 내부의 선택지 목록 등을 파싱하여
    # 후속 응답 정규화 과정에서 활용
    options = extract_options_from_prompt(prompt)

    # --------------------------------------------------
    # 4. LLM 응답 정규화
    # --------------------------------------------------
    # LLM 응답을 미리 정의된 옵션 기반으로
    # 표준 형태로 변환 (ex: Yes/No, 선택지 매핑 등)
    normalized = normalize_response(result, options)

    # --------------------------------------------------
    # 5. 결과 반환
    # --------------------------------------------------
    return {
        "success": True,
        "response": result,      # LLM 원본 응답
        "normalized": normalized, # 후처리된 응답
    }