import json
import re
import ollama

from app.enums.asset import AssetCategory, AssetType
from app.schemas.asset import ItemDefinitionRequest
from app.services.chroma_service import ChromaService


class AssetService:
    def __init__(self):
        self.ollama_client = ollama.Client(host="http://ollama:11434")
        self.llm_model = "llama3.2:latest"
        self.chroma_service = ChromaService()
        self.search_top_k = 5
        self.max_distance = 0.75

    def _extract_json_block(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        return text

    def _normalize_category(self, value: str, asset_name: str = "") -> str:
        valid = [e.value for e in AssetCategory]
        aliases = {
            "CAN": "CAN_Communication_Data",
            "CAN data": "CAN_Communication_Data",
            "Ethernet": "Ethernet_Communication_Data",
            "WiFi": "Wi-Fi_Communication_Data",
            "Wi-Fi": "Wi-Fi_Communication_Data",
            "Bluetooth": "Bluetooth_Communication_Data",
            "Cellular": "Cellular_Communication_Data",
            "GPS": "GPS_signal_Data",
            "GNSS": "GPS_signal_Data",
            "ECU": "Stored_Data_in_ECU_system",
            "ECU system": "Stored_Data_in_ECU_system",
            "Firmware": "Firmware_File",
        }

        asset_lower = asset_name.lower()

        if "cellular" in asset_lower or "lte" in asset_lower or "modem" in asset_lower:
            return "Cellular_Communication_Data"
        if "bluetooth" in asset_lower:
            return "Bluetooth_Communication_Data"
        if "wifi" in asset_lower or "wi-fi" in asset_lower or "wireless" in asset_lower:
            return "Wi-Fi_Communication_Data"
        if "gps" in asset_lower or "gnss" in asset_lower or "position" in asset_lower or "location" in asset_lower:
            return "GPS_signal_Data"
        if "nfc" in asset_lower:
            return "NFC_Communication_Data"
        if "rf" in asset_lower or "lf" in asset_lower or "key fob" in asset_lower:
            return "RF_LF_signal_Data"
        if "v2v" in asset_lower:
            return "V2V_communication_Data"
        if "firmware" in asset_lower or "ota package" in asset_lower or "update package" in asset_lower:
            return "Firmware_File"
        if (
            "log" in asset_lower
            or "diagnostic" in asset_lower
            or "parameter" in asset_lower
            or "configuration" in asset_lower
            or "routing rule" in asset_lower
            or "filtering rule" in asset_lower
            or "policy" in asset_lower
            or "certificate" in asset_lower
            or "credential" in asset_lower
            or "key" in asset_lower
        ):
            return "Stored_Data_in_ECU_system"

        if value in valid:
            return value

        return aliases.get(value, "")

    def _normalize_type(self, value: str, asset_name: str = "") -> str:
        valid = [e.value for e in AssetType]
        aliases = {
            "Driving Data": "Driving Data (e.g. mileage, driving speed, driving directions, etc.)",
            "Config Parameters": "Configuration parameters (vehicle’s key functions, such as brake data, airbag deployed threshold, etc)",
            "Configuration Parameter": "Configuration parameters (vehicle’s key functions, such as brake data, airbag deployed threshold, etc)",
            "Diagnostic Data": "System diagnostic data",
            "Logs": "Log Data",
            "Firmware": "Data in Firmware",
            "Cryptographic Key": "Cryptographic Keys",
        }

        asset_lower = asset_name.lower()

        if "key" in asset_lower or "certificate" in asset_lower or "credential" in asset_lower or "token" in asset_lower:
            return "Cryptographic Keys"
        if "log" in asset_lower:
            return "Log Data"
        if "diagnostic" in asset_lower or "obd" in asset_lower:
            return "System diagnostic data"
        if (
            "parameter" in asset_lower
            or "configuration" in asset_lower
            or "calibration" in asset_lower
            or "routing rule" in asset_lower
            or "filtering rule" in asset_lower
            or "policy" in asset_lower
            or "access control" in asset_lower
        ):
            return "Configuration parameters (vehicle’s key functions, such as brake data, airbag deployed threshold, etc)"
        if "firmware" in asset_lower or "ota package" in asset_lower or "update package" in asset_lower or "manifest" in asset_lower:
            return "Data in Firmware"
        if "position" in asset_lower or "gnss" in asset_lower or "gps" in asset_lower or "location" in asset_lower:
            return "Driving Data (e.g. mileage, driving speed, driving directions, etc.)"

        # 너무 넓어서 제거:
        # if "communication" in asset_lower or "telematics" in asset_lower or "signal" in asset_lower:
        #     return "Driving Data (e.g. mileage, driving speed, driving directions, etc.)"

        if value in valid:
            return value

        return aliases.get(value, "")

    def _build_retrieval_queries(self, request: ItemDefinitionRequest) -> list[str]:
        queries = []

        if request.full_name:
            queries.append(request.full_name)

        for fn in request.functions[:5]:
            queries.append(f"{request.full_name} {fn.name}")
            queries.append(f"{fn.name} {fn.explanation}")

        function_names = " ".join([fn.name for fn in request.functions[:6]])
        if function_names:
            queries.append(f"{request.full_name} {function_names}")

        # 자산 중심 확장 쿼리 추가
        asset_keywords = [
            "asset",
            "data",
            "configuration",
            "parameter",
            "credential",
            "certificate",
            "key",
            "token",
            "log",
            "diagnostic",
            "routing",
            "filtering",
            "policy",
            "command",
            "update package",
            "manifest",
        ]

        for keyword in asset_keywords:
            queries.append(f"{request.full_name} {keyword}")

        return list(dict.fromkeys([q.strip() for q in queries if q.strip()]))

    def _retrieve_context(self, request: ItemDefinitionRequest) -> str:
        queries = self._build_retrieval_queries(request)

        collected = []
        seen_docs = set()

        for query in queries:
            try:
                result = self.chroma_service.query_documents(
                    query_text=query,
                    top_k=self.search_top_k
                )

                documents = result.get("documents", [[]])[0]
                metadatas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0]

                for doc, metadata, distance in zip(documents, metadatas, distances):
                    text = str(doc).strip()
                    distance = float(distance)

                    if not text:
                        continue
                    if distance > self.max_distance:
                        continue
                    if text in seen_docs:
                        continue

                    seen_docs.add(text)
                    collected.append({
                        "text": text,
                        "source": (metadata or {}).get("source", "unknown"),
                        "distance": distance
                    })

            except Exception as e:
                print(f"[rag] query failed: {query} -> {e}")

        collected = sorted(collected, key=lambda x: x["distance"])[:5]

        context_blocks = []
        for i, item in enumerate(collected, start=1):
            context_blocks.append(
                f"[Context {i}] source={item['source']} distance={round(item['distance'], 4)}\n{item['text'][:700]}"
            )

        return "\n\n".join(context_blocks)

    def generate_assets(self, request: ItemDefinitionRequest) -> dict:
        category_values = [e.value for e in AssetCategory]
        type_values = [e.value for e in AssetType]

        functions_text = "\n".join(
            [f"- {f.name}: {f.explanation}" for f in request.functions]
        )
        assumptions_text = "\n".join([f"- {a}" for a in request.assumptions])

        retrieved_context = self._retrieve_context(request)

        prompt = f"""
You are an automotive cybersecurity TARA expert.

Return JSON only.
Do not explain.
Do not use markdown.

Task:
Identify important cyber assets for the given ECU/item.

Asset selection principles:
- Select assets that are stored, processed, transmitted, configured, or protected by the ECU itself.
- Prefer ECU-intrinsic assets over narrow example signals from other ECUs/domains.
- Prefer important cyber assets such as configuration data, routing/filtering data, credentials, certificates, keys, logs, command data, diagnostic data, OTA-related data, and core communication data.
- Do not list random example signals unless they are clearly core assets of this ECU.
- Use generalized asset names when appropriate.
- Avoid duplicates.
- Use the retrieved context only as supporting reference.
- Do not invent assets from unrelated ECUs/domains.

Special guidance:
- For gateway ECUs, prefer routing, filtering, diagnostic routing, policy, access control, forwarded network communication, and gateway logs over domain-specific signals like brake pressure.
- For telematics ECUs, prefer cellular communication, GNSS/location, remote command data, OTA package data, credentials/certificates, configuration parameters, and diagnostic logs.
- If an interface is not clearly supported by the input or context, do not include it.

Rules:
- Use only the allowed category values.
- Use only the allowed type values.
- Return 3 to 8 important assets.

Allowed category values only:
{json.dumps(category_values, ensure_ascii=False)}

Allowed type values only:
{json.dumps(type_values, ensure_ascii=False)}

Input:
ITEM: {request.item}
Full Name: {request.full_name}
Security Level: {request.security_level}

Functions:
{functions_text}

Assumptions:
{assumptions_text}

Retrieved Context:
{retrieved_context}

Output format:
{{
  "item": "{request.item}",
  "full_name": "{request.full_name}",
  "generated_assets": [
    {{
      "asset_name": "Gateway Routing Configuration",
      "category": "Stored_Data_in_ECU_system",
      "type": "Configuration parameters (vehicle’s key functions, such as brake data, airbag deployed threshold, etc)"
    }},
    {{
      "asset_name": "Diagnostic Log Data",
      "category": "Stored_Data_in_ECU_system",
      "type": "Log Data"
    }}
  ]
}}
"""

        response = self.ollama_client.generate(
            model=self.llm_model,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0,
                "num_predict": 700,
                "num_ctx": 4096
            }
        )

        raw_text = response.get("response", "").strip()
        json_text = self._extract_json_block(raw_text)

        try:
            result = json.loads(json_text)
        except Exception as e:
            return {
                "item": request.item,
                "full_name": request.full_name,
                "generated_assets": [],
                "error": f"JSON 파싱 실패: {str(e)}",
                "raw_response": raw_text
            }

        cleaned_assets = []
        seen = set()

        for asset in result.get("generated_assets", []):
            asset_name = str(asset.get("asset_name", "")).strip()
            category = self._normalize_category(
                str(asset.get("category", "")).strip(),
                asset_name
            )
            asset_type = self._normalize_type(
                str(asset.get("type", "")).strip(),
                asset_name
            )

            if not asset_name or not category or not asset_type:
                continue

            key = (asset_name.lower(), category, asset_type)
            if key in seen:
                continue
            seen.add(key)

            cleaned_assets.append({
                "asset_name": asset_name,
                "category": category,
                "type": asset_type,
            })

        return {
            "item": request.item,
            "full_name": request.full_name,
            "generated_assets": cleaned_assets
        }