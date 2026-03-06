from pydantic import BaseModel, Field


class AssetInput(BaseModel):
    """
    Asset Identification 분석 입력 스키마

    - 시스템 경계, 기능 목록, 가정 조건을 하나의 입력 객체로 관리한다.
    - assumptions는 기본값으로 빈 리스트를 사용하되,
      mutable default 이슈를 피하기 위해 default_factory를 사용한다.
    """

    item_boundary: dict  # 분석 대상 시스템 경계 정보
    functions: list[dict]  # 분석 대상 기능 목록
    assumptions: list[str] = Field(default_factory=list)  # 분석 가정 조건 목록


class AssetIdentificationRequest(BaseModel):
    """
    Asset Identification API 요청 스키마
    """

    input: AssetInput  # 실제 분석 입력 데이터