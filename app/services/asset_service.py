from app.prompts.asset_identification import build_asset_identification_prompt
from app.core.ollama_client import call_ollama
from app.utils.json_parser import (
    parse_llm_json,
    normalize_asset_identification_result,
    validate_asset_identification_result,
)


def run_asset_identification(payload: dict):
    """
    Asset Identification 분석 파이프라인 실행 함수

    - 입력 payload를 기반으로 LLM 프롬프트를 생성합니다.
    - Ollama를 호출하여 Asset Identification 결과를 생성합니다.
    - LLM 응답을 JSON으로 파싱한 뒤, 표준 형식으로 정규화하고 최종 검증합니다.
    - 검증이 완료된 결과만 반환하여 후속 로직의 안정성을 보장합니다.

    Args:
        payload (dict): item boundary, functions, assumptions 등을 포함한 입력 데이터

    Returns:
        dict: Asset Identification 처리 결과
            {
                "success": True,
                "result": normalized_result
            }

    Raises:
        ValueError: 모델 응답이 JSON 형식에 맞지 않거나 검증에 실패한 경우
    """

    # --------------------------------------------------
    # 1. Asset Identification 전용 프롬프트 생성
    # --------------------------------------------------
    # 입력 payload를 LLM이 이해할 수 있는 프롬프트 문자열로 변환
    prompt = build_asset_identification_prompt(payload)

    # --------------------------------------------------
    # 2. LLM(Ollama) 호출
    # --------------------------------------------------
    # 생성된 프롬프트를 기반으로 모델 응답 수신
    result = call_ollama(prompt)

    try:
        # --------------------------------------------------
        # 3. LLM 응답 JSON 파싱
        # --------------------------------------------------
        # 모델 응답 문자열에서 JSON 객체 추출
        parsed = parse_llm_json(result)

        # --------------------------------------------------
        # 4. 결과 정규화
        # --------------------------------------------------
        # 키 형식, 필드 구조 등 후속 처리 가능한 표준 스키마로 변환
        normalized = normalize_asset_identification_result(parsed)

        # --------------------------------------------------
        # 5. 최종 결과 검증
        # --------------------------------------------------
        # 필수 필드 존재 여부, properties 구조, 값 유효성 등을 검증
        validate_asset_identification_result(normalized)

        # --------------------------------------------------
        # 6. 검증 완료 결과 반환
        # --------------------------------------------------
        return {
            "success": True,
            "result": normalized,
        }

    except ValueError as e:
        # 모델이 JSON 형식을 지키지 못했거나
        # 정규화/검증 단계에서 실패한 경우 원본 응답을 포함해 예외 전달
        raise ValueError(
            f"모델이 올바른 JSON을 반환하지 않았습니다: {str(e)} | raw_response={result}"
        ) from e