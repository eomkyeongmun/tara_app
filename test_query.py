from app.services.chroma_service import ChromaService


def main():
    queries = [
        "Telematics Control Unit cellular modem GNSS Wi-Fi remote vehicle OTA",
        "TCU telematics cellular remote communication",
        "vehicle telematics module OTA GNSS modem"
    ]

    chroma_service = ChromaService()

    for query in queries:
        print("\n" + "=" * 80)
        print(f"[QUERY] {query}")

        results = chroma_service.query_documents(query, top_k=5)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None

            print(f"\n[{i+1}] distance={distance}")
            print(f"metadata={metadata}")
            print(doc[:1000])


if __name__ == "__main__":
    main()