from app.services.chroma_service import ChromaService


def main():
    chroma = ChromaService()

    query = "Electronic Brake Controller brake control asset"
    result = chroma.query_documents(query_text=query, top_k=5)

    print("===== RAW QUERY RESULT =====")
    print(result)

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    print("\n===== PARSED RESULT =====")
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        print(f"\n--- result {i} ---")
        print("distance:", dist)
        print("metadata:", meta)
        print("text preview:", doc[:500])


if __name__ == "__main__":
    main()