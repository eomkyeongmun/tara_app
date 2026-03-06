from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.auth import LoginRequest
from app.schemas.analysis import AnalyzeRequest
from app.schemas.tara import AssetIdentificationRequest

from app.services.auth_service import login_user
from app.services.analysis_service import analyze_text
from app.services.asset_service import run_asset_identification

app = FastAPI()


@app.get("/")
def health():
    """
    애플리케이션 헬스체크 엔드포인트

    - 운영 환경에서는 내부 설정값을 노출하지 않고
      최소 상태 정보만 반환하는 것이 안전하다.
    """
    return {"ok": True}


@app.post("/login")
def login(data: LoginRequest):
    """
    로그인 API
    """
    try:
        return login_user(data.username, data.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze(data: AnalyzeRequest):
    """
    일반 텍스트 분석 API
    """
    try:
        return analyze_text(data.text)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.post("/asset-identification")
def asset_identification(data: AssetIdentificationRequest):
    """
    Asset Identification API
    """
    try:
        # 실제 분석 payload만 service로 전달
        return run_asset_identification(data.input.model_dump())
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )