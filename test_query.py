from app.services.chroma_service import ChromaService


def main():
    query = "위험 분석이란 무엇인가?"

    chroma_service = ChromaService()
    results = chroma_service.query_documents(query, top_k=3)

    print("=== 검색 결과 ===")
    for i, doc in enumerate(results["documents"][0], start=1):
        print(f"\n[{i}] {doc}")


if __name__ == "__main__":
    main()