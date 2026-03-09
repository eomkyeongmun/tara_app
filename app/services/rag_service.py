import ollama
from app.services.chroma_service import ChromaService


class RagService:
    def __init__(self):
        self.chroma_service = ChromaService()
        self.ollama_client = ollama.Client(host="http://ollama:11434")
        self.llm_model = "llama3.2:latest"
        self.max_distance = 0.70

    def _build_search_query(self, question: str) -> str:
        if question is None:
            return ""
        return question.strip()

    def _expand_query(self, search_query: str) -> list[str]:
        q = search_query.strip()
        if not q:
            return []

        candidates = [q]
        lower_q = q.lower()

        if "tara" in lower_q or "위협 분석" in q or "위험 평가" in q:
            candidates.extend([
                "TARA 정의",
                "위협 분석 및 위험 평가 정의",
                "Threat Analysis and Risk Assessment definition",
                "TARA란",
                "TARA 개요",
            ])

        if "정의" in q or "란" in q or "무엇" in q:
            candidates.extend([
                q.replace("무엇", "정의"),
                q.replace("란", "정의"),
            ])

        unique = []
        seen = set()

        for c in candidates:
            c = c.strip()
            if c and c not in seen:
                unique.append(c)
                seen.add(c)

        return unique

    def _rerank_results(self, question: str, results: list[dict], top_k: int = 5) -> list[dict]:
        q = question.lower()

        def score_item(item):
            content = item["content"].lower()
            distance = item["distance"] if item["distance"] is not None else 999.0

            score = -distance

            if "정의" in q or "란" in q or "무엇" in q:
                if "정의" in content:
                    score += 0.20
                if "란" in content:
                    score += 0.15
                if "개요" in content:
                    score += 0.10
                if "목적" in content:
                    score += 0.08

            if "tara" in q or "위협 분석" in q or "위험 평가" in q:
                if "tara" in content:
                    score += 0.20
                if "위협 분석" in content:
                    score += 0.15
                if "위험 평가" in content:
                    score += 0.15
                if "threat analysis" in content:
                    score += 0.12
                if "risk assessment" in content:
                    score += 0.12

            noisy_keywords = ["network", "adjacent", "local", "bluetooth", "obd", "셀룰러"]
            for kw in noisy_keywords:
                if kw in content:
                    score -= 0.03

            return score

        dedup = {}
        for item in results:
            key = item["content"].strip()
            if key not in dedup:
                dedup[key] = item
            else:
                prev_dist = dedup[key]["distance"] if dedup[key]["distance"] is not None else 999.0
                curr_dist = item["distance"] if item["distance"] is not None else 999.0
                if curr_dist < prev_dist:
                    dedup[key] = item

        reranked = sorted(dedup.values(), key=score_item, reverse=True)
        return reranked[:top_k]

    def generate_answer(self, user_question: str, top_k: int = 5) -> dict:
        search_query = self._build_search_query(user_question)

        if not search_query:
            return {
                "question": user_question,
                "search_query": "",
                "answer": "질문이 비어 있습니다.",
                "references": []
            }

        expanded_queries = self._expand_query(search_query)
        print(f"[user_question] {user_question}")
        print(f"[search_query] {search_query}")
        print(f"[expanded_queries] {expanded_queries}")

        merged_results = []

        for query in expanded_queries:
            print(f"[search] {query}")
            results = self.chroma_service.query_documents(query, top_k=top_k)

            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc in enumerate(documents):
                metadata = metadatas[i] if i < len(metadatas) else {}
                distance = distances[i] if i < len(distances) else None

                print(
                    f"[retrieval] query={query}, rank={i + 1}, "
                    f"distance={distance}, metadata={metadata}"
                )

                if distance is None or distance <= self.max_distance:
                    merged_results.append({
                        "query": query,
                        "content": doc,
                        "metadata": metadata,
                        "distance": distance
                    })

        if not merged_results:
            return {
                "question": user_question,
                "search_query": search_query,
                "answer": "관련 참고 문서를 찾지 못했습니다.",
                "references": []
            }

        final_results = self._rerank_results(user_question, merged_results, top_k=top_k)

        if not final_results:
            return {
                "question": user_question,
                "search_query": search_query,
                "answer": "질문과 충분히 가까운 참고 문서를 찾지 못했습니다.",
                "references": []
            }

        context_parts = []
        references = []

        for i, item in enumerate(final_results):
            context_parts.append(f"[문서 {i + 1}]\n{item['content']}")
            references.append({
                "rank": i + 1,
                "query": item["query"],
                "metadata": item["metadata"],
                "distance": item["distance"],
                "content": item["content"]
            })

        context = "\n\n".join(context_parts)

        prompt = f"""
너는 자동차 사이버보안 문서를 기반으로만 답하는 한국어 문서 QA 비서다.

반드시 아래 규칙을 따른다.

[규칙]
1. 반드시 한국어로만 답한다.
2. 아래 참고 문서에 있는 내용만 사용한다.
3. 참고 문서에 없는 내용은 절대 추측하지 않는다.
4. 질문에 대한 정의를 참고 문서에서 직접 확인할 수 없으면 반드시 아래 문장으로만 답한다.
   - "참고 문서 기준으로 명확히 확인되지 않습니다."
5. 질문이 정의형이면 아래 형식을 반드시 지킨다.
   - 정의: 한 줄 정의
   - 설명: 1~2문장 보충 설명
6. 답변은 문서 표현을 최대한 그대로 우선 사용한다.
7. 여러 문서가 섞여 애매하면 공통적으로 확인되는 내용만 답한다.
8. 참고 문서가 정의가 아니라 예시/부가설명 위주면 정의를 만들어내지 말고 확인되지 않는다고 답한다.
9. "국제 표준이다", "지침이다"처럼 문서 전체 설명을 질문 대상의 정의처럼 오해해서 답하지 않는다.
10. 약어 질문이면 약어의 풀네임과 문서 내 정의를 우선 확인한다.

[질문]
{user_question}

[참고 문서]
{context}

[답변 형식]
정의:
설명:
"""

        response = self.ollama_client.generate(
            model=self.llm_model,
            prompt=prompt,
            options={
                "temperature": 0.0,
                "num_predict": 120,
                "num_ctx": 2048
            }
        )

        answer = response.get("response", "").strip()

        if not answer:
            answer = "답변을 생성하지 못했습니다."

        return {
            "question": user_question,
            "search_query": search_query,
            "answer": answer,
            "references": references
        }