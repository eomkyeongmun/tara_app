import re
import difflib


def extract_options_from_prompt(prompt_text: str):
    """
    프롬프트 문자열에서 선택 옵션 목록을 추출한다.

    - 프롬프트 내 "Options (choose one):" 형태의 섹션을 찾아
      해당 줄에 나열된 옵션을 파싱한다.
    - 옵션은 쉼표(,) 기준으로 분리하여 리스트로 반환한다.

    예시:
        Options (choose one):
        Yes, No, Unknown

    Args:
        prompt_text (str): LLM 호출에 사용된 프롬프트 문자열

    Returns:
        list[str]: 선택 가능한 옵션 리스트
    """
    match = re.search(r"Options \(choose one\):\s*\n([^\n]+)", prompt_text)
    if not match:
        return []

    raw_line = match.group(1).strip()

    # 쉼표 기준으로 옵션 분리 후 공백 제거
    return [opt.strip() for opt in raw_line.split(",") if opt.strip()]


def normalize_response(raw_response: str, options: list[str]) -> str:
    """
    LLM 원본 응답을 선택 옵션 기반으로 정규화한다.

    처리 단계:
    1. 옵션이 없는 경우 "Unknown" 반환
    2. 응답과 옵션의 정확한 일치 여부 확인
    3. 옵션 문자열이 응답에 포함되는지 검사
    4. 유사 문자열 매칭(difflib)을 이용한 근사 매칭
    5. 어떤 조건에도 맞지 않으면 "Unknown" 반환

    Args:
        raw_response (str): LLM 원본 응답 텍스트
        options (list[str]): 허용 가능한 선택 옵션 목록

    Returns:
        str: 정규화된 옵션 값 (options 중 하나 또는 "Unknown")
    """

    # 옵션이 없으면 정규화 불가능
    if not options:
        return "Unknown"

    # 비교를 위해 소문자 변환 및 공백 제거
    raw = (raw_response or "").lower().strip()
    options_lower = [opt.lower() for opt in options]

    # --------------------------------------------------
    # 1. 완전 일치 검사
    # --------------------------------------------------
    for i, opt in enumerate(options_lower):
        if raw == opt:
            return options[i]

    # --------------------------------------------------
    # 2. 포함 관계 검사
    # --------------------------------------------------
    # 예: "the answer is yes" → "Yes"
    for i, opt in enumerate(options_lower):
        if opt and opt in raw:
            return options[i]

    # --------------------------------------------------
    # 3. 유사도 기반 매칭
    # --------------------------------------------------
    # 철자 오류나 약간의 변형을 보정
    best_match = difflib.get_close_matches(raw, options_lower, n=1, cutoff=0.5)
    if best_match:
        idx = options_lower.index(best_match[0])
        return options[idx]

    # --------------------------------------------------
    # 4. 매칭 실패
    # --------------------------------------------------
    return "Unknown"