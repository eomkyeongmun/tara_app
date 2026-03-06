import json
import re


# Asset Identification 결과에서 필수로 포함되어야 하는 속성 키
REQUIRED_PROPERTY_KEYS = ["C", "I", "A1", "A2", "A3"]

# properties 값으로 허용하는 값
# - O : 해당 속성이 중요함
# - - : 해당 없음 / 불확실 / 미적용
ALLOWED_PROPERTY_VALUES = ["O", "-"]


def clean_llm_response(text: str) -> str:
    """
    LLM 원본 응답 문자열을 JSON 파싱 가능한 형태로 1차 정리한다.

    - 빈 응답 여부를 검증한다.
    - LLM이 종종 포함하는 markdown 코드블록(```json, ```)을 제거한다.
    - JSON 외곽의 불필요한 포맷팅을 최소화하여 후속 파싱 성공률을 높인다.

    Args:
        text (str): LLM 원본 응답 문자열

    Returns:
        str: 1차 정리된 응답 문자열

    Raises:
        ValueError: 응답이 비어 있는 경우
    """
    if not text or not text.strip():
        raise ValueError("빈 응답입니다.")

    cleaned = text.strip()

    # markdown 코드블록 표식 제거
    cleaned = re.sub(r"```json", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    return cleaned.strip()


def extract_first_json_object(text: str) -> str:
    """
    문자열 내에서 첫 번째 완전한 JSON 객체({ ... })만 추출한다.

    - LLM이 JSON 앞뒤로 설명문을 붙이는 경우를 대비한 보조 파서다.
    - 문자열 내부 따옴표, escape 문자까지 고려하여 중괄호 균형을 맞춘다.

    Args:
        text (str): JSON 이외 텍스트가 포함될 수 있는 응답 문자열

    Returns:
        str: 추출된 JSON 객체 문자열

    Raises:
        ValueError: JSON 시작점 또는 완전한 JSON 객체를 찾지 못한 경우
    """
    start = text.find("{")
    if start == -1:
        raise ValueError("응답에서 JSON 시작('{')을 찾을 수 없습니다.")

    brace_count = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if not in_string:
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i + 1]

    raise ValueError("응답에서 완전한 JSON 객체를 찾을 수 없습니다.")


def parse_llm_json(raw_response: str) -> dict:
    """
    LLM 응답 문자열을 JSON 객체(dict)로 파싱한다.

    처리 순서:
    1. 코드블록 제거 등 1차 정리
    2. 전체 문자열을 바로 JSON 파싱 시도
    3. 실패하면 첫 번째 JSON 객체만 추출 후 재파싱
    4. 최상위 타입이 dict인지 검증

    Args:
        raw_response (str): LLM 원본 응답

    Returns:
        dict: 파싱된 최상위 JSON 객체

    Raises:
        ValueError: JSON 파싱 실패 또는 최상위 타입이 dict가 아닌 경우
    """
    cleaned = clean_llm_response(raw_response)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        json_text = extract_first_json_object(cleaned)
        parsed = json.loads(json_text)

    if not isinstance(parsed, dict):
        raise ValueError("최상위 JSON은 객체(dict)여야 합니다.")

    return parsed


def normalize_asset_identification_result(data: dict) -> dict:
    """
    Asset Identification 결과를 표준 스키마에 맞게 정규화한다.

    - 누락된 최상위 키(section, version, rows)에 기본값을 채운다.
    - rows가 list인지 확인한다.
    - 각 row의 asset/category/type/properties 구조를 정리한다.
    - properties는 필수 키(C, I, A1, A2, A3)를 모두 가지도록 보정한다.
    - 허용되지 않은 properties 값은 모두 '-'로 치환한다.

    Args:
        data (dict): 파싱된 LLM 결과 객체

    Returns:
        dict: 표준 스키마 형태로 정규화된 결과

    Raises:
        ValueError: 최상위 구조가 올바르지 않은 경우
    """
    if not isinstance(data, dict):
        raise ValueError("최상위 JSON은 객체(dict)여야 합니다.")

    # 최상위 기본값 보정
    data.setdefault("section", "asset_identification")
    data.setdefault("version", "1.0")
    data.setdefault("rows", [])

    if not isinstance(data["rows"], list):
        raise ValueError("rows는 배열(list)이어야 합니다.")

    normalized_rows = []

    for idx, row in enumerate(data["rows"]):
        if not isinstance(row, dict):
            continue

        asset = row.get("asset", "")
        category = row.get("category", "")
        row_type = row.get("type", "")
        props = row.get("properties", {})

        if not isinstance(props, dict):
            props = {}

        # properties 필수 키 보정 + 허용값 외 값 정리
        normalized_props = {}
        for key in REQUIRED_PROPERTY_KEYS:
            value = props.get(key, "-")
            if value not in ALLOWED_PROPERTY_VALUES:
                value = "-"
            normalized_props[key] = value

        normalized_row = {
            "asset": asset.strip() if isinstance(asset, str) else "",
            "category": category.strip() if isinstance(category, str) else "",
            "type": row_type.strip() if isinstance(row_type, str) else "",
            "properties": normalized_props,
        }

        normalized_rows.append(normalized_row)

    data["rows"] = normalized_rows
    return data


def validate_asset_identification_result(data: dict) -> None:
    """
    정규화된 Asset Identification 결과가 최종 스키마 요구사항을 만족하는지 검증한다.

    검증 항목:
    - 최상위 필수 필드 존재 여부
    - section 값 고정 여부
    - version / rows 타입 검증
    - 각 row의 필수 필드 존재 여부
    - asset/category/type 값이 비어 있지 않은 문자열인지 확인
    - properties 구조 및 허용값 검증

    Args:
        data (dict): 정규화된 결과 객체

    Raises:
        ValueError: 스키마 또는 값 검증 실패 시
    """
    required_top_keys = ["section", "version", "rows"]
    for key in required_top_keys:
        if key not in data:
            raise ValueError(f"최상위 필드 '{key}' 가 없습니다.")

    if data["section"] != "asset_identification":
        raise ValueError("section 값은 'asset_identification' 이어야 합니다.")

    if not isinstance(data["version"], str):
        raise ValueError("version은 문자열이어야 합니다.")

    if not isinstance(data["rows"], list):
        raise ValueError("rows는 배열(list)이어야 합니다.")

    for idx, row in enumerate(data["rows"]):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{idx}] 는 객체여야 합니다.")

        for key in ["asset", "category", "type", "properties"]:
            if key not in row:
                raise ValueError(f"rows[{idx}]에 '{key}' 필드가 없습니다.")

        if not isinstance(row["asset"], str) or not row["asset"].strip():
            raise ValueError(f"rows[{idx}].asset 는 비어있지 않은 문자열이어야 합니다.")

        if not isinstance(row["category"], str) or not row["category"].strip():
            raise ValueError(f"rows[{idx}].category 는 비어있지 않은 문자열이어야 합니다.")

        if not isinstance(row["type"], str) or not row["type"].strip():
            raise ValueError(f"rows[{idx}].type 는 비어있지 않은 문자열이어야 합니다.")

        props = row["properties"]
        if not isinstance(props, dict):
            raise ValueError(f"rows[{idx}].properties 는 객체여야 합니다.")

        for pkey in REQUIRED_PROPERTY_KEYS:
            if pkey not in props:
                raise ValueError(f"rows[{idx}].properties 에 '{pkey}' 필드가 없습니다.")
            if props[pkey] not in ALLOWED_PROPERTY_VALUES:
                raise ValueError(
                    f"rows[{idx}].properties.{pkey} 값은 'O' 또는 '-' 여야 합니다."
                )