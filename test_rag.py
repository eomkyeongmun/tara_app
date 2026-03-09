import time

from app.services.rag_service import RagService


def main():
    rag_service = RagService()

    question = "TARA의 프로세스를 Item definition 부터 끝까지 설명해줘"

    print(f"질문: {question}")
    start = time.time()

    result = rag_service.generate_answer(question, top_k=5)

    print("\n=== 검색 질의 ===")
    print(result.get("search_query"))

    print("\n=== 답변 ===")
    print(result["answer"])

    print("\n=== 참고 청크 정보 ===")
    for ref in result.get("references", []):
        print({
            "rank": ref.get("rank"),
            "query": ref.get("query"),
            "metadata": ref.get("metadata"),
            "distance": ref.get("distance"),
            "content": ref.get("content"),
        })

    print("\n=== 실행 시간 ===")
    print(f"전체 실행 시간: {time.time() - start:.2f}초")


if __name__ == "__main__":
    main()