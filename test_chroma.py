from pathlib import Path
from app.utils.text_chunker import chunk_text


def main():
    txt_path = "debug_cleaned.txt"

    text = Path(txt_path).read_text(encoding="utf-8")
    chunks = chunk_text(text)

    Path("debug_chunks.txt").write_text(
        "\n\n".join([f"===== CHUNK {i} =====\n{chunk}" for i, chunk in enumerate(chunks)]),
        encoding="utf-8"
    )

    print("전처리 txt 글자수:", len(text))
    print("총 청크 수:", len(chunks))

    target_indexes = [18, 28, 42]

    for idx in target_indexes:
        if 0 <= idx < len(chunks):
            print(f"\n##### chunk {idx} #####")
            print(chunks[idx][:1000])
            print("-" * 80)


if __name__ == "__main__":
    main()