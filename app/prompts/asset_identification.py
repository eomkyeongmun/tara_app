import json


def build_asset_identification_prompt(payload: dict) -> str:
    """
    Asset Identification 단계용 LLM 프롬프트를 생성하는 함수

    - 입력 payload를 JSON 문자열로 직렬화한 뒤, 고정된 지시문(prompt template)에 삽입합니다.
    - LLM이 자동차 사이버보안 TARA 문맥에서 자산 식별 결과를 생성하도록 유도합니다.
    - 출력 형식을 엄격한 JSON 1개 객체로 제한하여 후속 파싱 안정성을 높입니다.

    Args:
        payload (dict): item boundary, functions, assumptions 등을 포함한 입력 데이터

    Returns:
        str: LLM 호출에 사용할 최종 프롬프트 문자열
    """

    # 입력 payload를 사람이 읽기 쉬운 형태의 JSON 문자열로 변환
    # - ensure_ascii=False: 한글이 유니코드 이스케이프(\uXXXX)로 깨지지 않도록 처리
    # - indent=2: 프롬프트 내 입력 데이터 가독성 확보
    input_json = json.dumps(payload, ensure_ascii=False, indent=2)

    # LLM 프롬프트 템플릿
    # - 역할(Role): 자동차 사이버보안 TARA 분석 전문가
    # - 목표(Task): functions 기준으로 asset identification 수행
    # - 제약(Constraints): JSON 외 텍스트 출력 금지, properties 필드 강제
    # - 스키마(Schema): 후속 JSON 파싱 가능하도록 출력 구조 고정
    #
    # 이 프롬프트는 "출력 품질"보다 "출력 형식 안정성"을 더 우선하는 설계다.
    # 즉, LLM이 자유롭게 설명하지 못하도록 강하게 제한하고,
    # 반드시 정형화된 JSON만 반환하도록 유도한다.
    return f"""
너는 자동차 사이버보안 TARA 분석 전문가다.

너의 임무는 입력된 시스템 경계(item boundary), 기능(functions), 가정(assumptions)을 분석하여
Asset Identification 결과를 생성하는 것이다.

[절대 규칙]
1. 출력은 반드시 JSON 객체 1개만 허용된다.
2. 출력의 첫 글자는 반드시 "{{" 여야 하고, 마지막 글자는 반드시 "}}" 여야 한다.
3. markdown, ```json 코드블록, 설명문, 주석, 부가 텍스트, 사족, 개행 후 추가 문장을 절대 출력하지 마라.
4. JSON 외의 어떤 문자도 출력하지 마라.
5. 모든 rows[*].properties 는 반드시 아래 5개 키를 모두 포함해야 한다.
   - "C"
   - "I"
   - "A1"
   - "A2"
   - "A3"
6. 위 5개 키를 절대 생략하지 마라.
7. properties의 값은 반드시 "O" 또는 "-" 둘 중 하나만 사용하라.
8. 판단이 어렵거나 해당이 없으면 설명하지 말고 반드시 "-"를 넣어라.
9. null, true, false, 숫자, 빈 문자열, 배열, 중첩 객체를 properties 값으로 사용하지 마라.
10. functions 개수가 N개이면 rows는 반드시 최소 N개 이상이어야 한다.
11. 서로 다른 기능은 절대 하나의 asset으로 합치지 말고 별도 row로 분리하라.
12. asset 이름은 item 이름만 그대로 쓰지 말고 기능 기반의 구체적인 자산명으로 작성하라.

[목표]
입력 데이터를 보고 자산(assets)을 식별하고, 각 자산에 대해 아래 항목을 채워라.
- asset
- category
- type
- properties

[속성 의미]
- C: Confidentiality(기밀성)
- I: Integrity(무결성)
- A1: Availability(일반 운영 가용성)
- A2: Availability(정비/진단 가용성)
- A3: Availability(안전 관련 가용성)

[판단 규칙]
1. 차량 네트워크 상의 메시지, 신호, 통신 payload는 통신 데이터 자산으로 식별한다.
   예: CAN_Communication_Data, Ethernet_Communication_Data
2. ECU 내부 저장 데이터, 로그, 설정값, 내부 기록은 저장 데이터 자산으로 식별한다.
   예: Stored_Data_in_ECU_system
3. 차량 제어에 직접 영향을 주는 명령 데이터는 무결성(I)이 중요하므로 "I": "O" 로 설정할 가능성이 높다.
4. 핵심 동작 수행에 필요한 데이터는 "A1": "O" 로 설정할 수 있다.
5. 정비/진단 목적 데이터는 "A2": "O" 로 설정할 수 있다.
6. 제동, 조향, 가속 등 안전 관련 제어에 영향을 줄 수 있으면 "A3": "O" 로 설정할 수 있다.
7. 중요하지 않거나 불확실한 속성은 반드시 "-" 로 표시한다.
8. item 자체는 시스템 경계 정보로 참고만 하고, 우선적으로 데이터/메시지/로그/설정값 자산을 식별하라.
9. functions의 각 항목을 기준으로 자산을 식별하라.
10. asset 이름은 기능 기반으로 구체적으로 작성하라.
    예:
    - Brake Command -> Brake Command Message
    - Steering Angle Signal -> Steering Angle Signal Data
    - Diagnostic Log 기록 -> Diagnostic Log Data
    - ECU Calibration Setting -> ECU Calibration Setting Data

[출력 JSON 스키마]
반드시 아래 구조를 그대로 따르라.

{{
  "section": "asset_identification",
  "version": "1.0",
  "rows": [
    {{
      "asset": "string",
      "category": "string",
      "type": "string",
      "properties": {{
        "C": "O 또는 -",
        "I": "O 또는 -",
        "A1": "O 또는 -",
        "A2": "O 또는 -",
        "A3": "O 또는 -"
      }}
    }}
  ]
}}

[출력 검증 체크리스트]
최종 응답을 만들기 전에 반드시 스스로 아래를 확인하라.
- JSON 객체 1개만 출력했는가?
- rows의 개수는 functions 개수 이상인가?
- 모든 row에 asset/category/type/properties가 있는가?
- 모든 row.properties에 C, I, A1, A2, A3 가 모두 존재하는가?
- properties의 값이 모두 "O" 또는 "-" 인가?
- 설명문이나 코드블록이 전혀 없는가?

[입력 데이터]
{input_json}

이제 최종 결과 JSON 객체 1개만 출력하라.
""".strip()