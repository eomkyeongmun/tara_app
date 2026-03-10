import uuid
from typing import Any

import ollama
import requests


class ChromaService:
    def __init__(self):
        self.base_url = "http://chromadb:8000"
        self.collection_name = "tara_docs"

        self.ollama_client = ollama.Client(host="http://ollama:11434")
        self.embed_model = "nomic-embed-text"

        # embedding 길이 제한 (충분히 크게)
        self.max_text_length = 2000

    # ---------------------------
    # 텍스트 정리
    # ---------------------------
    def _normalize_text(self, text: str) -> str:

        if text is None:
            raise ValueError("텍스트가 None입니다.")

        cleaned = text.strip()

        if not cleaned:
            raise ValueError("빈 텍스트는 임베딩할 수 없습니다.")

        if len(cleaned) > self.max_text_length:
            cleaned = cleaned[:self.max_text_length]

        return cleaned

    # ---------------------------
    # 단일 embedding
    # ---------------------------
    def get_embedding(self, text: str) -> list[float]:

        normalized = self._normalize_text(text)

        response = self.ollama_client.embed(
            model=self.embed_model,
            input=normalized
        )

        return response["embeddings"][0]

    # ---------------------------
    # batch embedding
    # ---------------------------
    def get_embeddings(self, texts: list[str]) -> list[list[float]]:

        if not texts:
            return []

        normalized_texts = []

        for text in texts:
            normalized_texts.append(self._normalize_text(text))

        print(f"[embed] batch size = {len(normalized_texts)}")

        response = self.ollama_client.embed(
            model=self.embed_model,
            input=normalized_texts
        )

        return response["embeddings"]

    # ---------------------------
    # Chroma heartbeat
    # ---------------------------
    def heartbeat(self) -> dict[str, Any]:

        response = requests.get(
            f"{self.base_url}/api/v2/heartbeat",
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    # ---------------------------
    # 컬렉션 생성
    # ---------------------------
    def create_collection(self) -> str:

        payload = {
            "name": self.collection_name,
            "metadata": {"description": "TARA RAG documents"}
        }

        response = requests.post(
            f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections",
            json=payload,
            timeout=30
        )

        if response.status_code not in (200, 201, 409):
            raise Exception(
                f"컬렉션 생성 실패: {response.status_code}, {response.text}"
            )

        return response.text

    # ---------------------------
    # 컬렉션 id
    # ---------------------------
    def get_collection_id(self) -> str:

        response = requests.get(
            f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{self.collection_name}",
            timeout=30
        )

        response.raise_for_status()

        return response.json()["id"]

    # ---------------------------
    # 컬렉션 삭제
    # ---------------------------
    def delete_collection_if_exists(self) -> bool:

        response = requests.delete(
            f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{self.collection_name}",
            timeout=30
        )

        if response.status_code in (200, 204):
            return True

        if response.status_code == 404:
            return False

        if "not found" in response.text.lower():
            return False

        raise Exception(
            f"컬렉션 삭제 실패: {response.status_code}, {response.text}"
        )

    # ---------------------------
    # 컬렉션 초기화
    # ---------------------------
    def reset_collection(self):

        self.delete_collection_if_exists()
        self.create_collection()

    # ---------------------------
    # 문서 추가
    # ---------------------------
    def add_documents(
        self,
        documents: list[str],
        source: str,
        doc_type: str = "standard",
        batch_size: int = 32
    ) -> dict[str, int]:

        if not documents:
            return {"added_count": 0}

        self.create_collection()

        collection_id = self.get_collection_id()

        total_added = 0

        for start in range(0, len(documents), batch_size):

            batch_docs_raw = documents[start:start + batch_size]

            batch_docs = []
            ids = []
            metadatas = []

            for i, doc in enumerate(batch_docs_raw):

                chunk_index = start + i

                try:

                    normalized = self._normalize_text(doc)

                    batch_docs.append(normalized)

                    ids.append(
                        f"{source}_{chunk_index}_{uuid.uuid4().hex[:8]}"
                    )

                    metadatas.append(
                        {
                            "source": source,
                            "chunk_index": chunk_index,
                            "doc_type": doc_type
                        }
                    )

                except ValueError as e:

                    print(f"[skip] chunk {chunk_index}: {e}")

            if not batch_docs:
                continue

            print(
                f"[batch] start={start} count={len(batch_docs)}"
            )

            batch_embeddings = self.get_embeddings(batch_docs)

            payload = {
                "ids": ids,
                "documents": batch_docs,
                "embeddings": batch_embeddings,
                "metadatas": metadatas
            }

            response = requests.post(
                f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection_id}/add",
                json=payload,
                timeout=120
            )

            response.raise_for_status()

            total_added += len(batch_docs)

        return {"added_count": total_added}

    # ---------------------------
    # 검색
    # ---------------------------
    def query_documents(
        self,
        query_text: str,
        top_k: int = 3
    ) -> dict[str, Any]:

        collection_id = self.get_collection_id()

        query_embedding = self.get_embedding(query_text)

        payload = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }

        response = requests.post(
            f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection_id}/query",
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        return response.json()
    
    def document_exists(self, source: str) -> bool:
        try:
            collection_id = self.get_collection_id()
        except Exception:
            return False

        payload = {
            "where": {
                "source": source
            },
            "limit": 1,
            "include": ["metadatas"]
        }

        response = requests.post(
            f"{self.base_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{collection_id}/get",
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        ids = data.get("ids", [])
        return bool(ids)