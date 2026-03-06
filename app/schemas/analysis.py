from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """
    분석 API 요청(Request Body) 스키마

    - FastAPI에서 클라이언트가 전달하는 JSON 요청을 검증하기 위해 사용됩니다.
    - Pydantic BaseModel을 상속하여 자동 타입 검증 및 데이터 파싱을 수행합니다.

    Fields:
        text (str): 분석 대상 텍스트 입력값
    """
    
    text: str  # 분석할 입력 텍스트 (LLM 또는 내부 분석 로직에서 사용)