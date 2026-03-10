from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.auth import LoginRequest
from app.schemas.analysis import AnalyzeRequest
from app.schemas.asset import ItemDefinitionRequest, AssetGenerationResponse

from app.services.auth_service import login_user
from app.services.analysis_service import analyze_text
from app.services.asset_service import AssetService as LLMAssetService

app = FastAPI()

llm_asset_service = LLMAssetService()


@app.get("/")
def health():
    return {"ok": True}


@app.post("/login")
def login(data: LoginRequest):
    try:
        return login_user(data.username, data.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze(data: AnalyzeRequest):
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


@app.post("/generate-assets/llm", response_model=AssetGenerationResponse)
def generate_assets_llm(request: ItemDefinitionRequest):
    try:
        return llm_asset_service.generate_assets(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )