from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    로그인 API 요청(Request Body) 스키마

    - 클라이언트가 로그인 시 전달하는 사용자 인증 정보를 정의합니다.
    - FastAPI + Pydantic을 통해 요청 데이터의 타입 검증을 자동으로 수행합니다.

    Fields:
        username (str): 사용자 로그인 아이디
        password (str): 사용자 비밀번호
    """

    username: str  # 사용자 계정 ID
    password: str  # 사용자 비밀번호