from typing import List
from pydantic import BaseModel, Field


class ItemFunction(BaseModel):
    name: str
    explanation: str


class ItemDefinitionRequest(BaseModel):
    item: str
    full_name: str
    security_level: str
    functions: List[ItemFunction] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class GeneratedAsset(BaseModel):
    asset_name: str
    category: str
    type: str


class AssetGenerationResponse(BaseModel):
    item: str
    full_name: str
    generated_assets: List[GeneratedAsset] = Field(default_factory=list)