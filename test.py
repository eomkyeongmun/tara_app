from pathlib import Path
from app.utils.pdf_parser import extract_text_from_pdf
from app.utils.text_cleaner import clean_text
from app.utils.text_chunker import chunk_text


DATASET_DIR = Path("tara_dataset")


def process_pdf(pdf_path):
    print(f"\n===== {pdf_path.name} 처리 =====")

    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(raw_text)
    chunks = chunk_text(cleaned_text)

    print("원본 글자수:", len(raw_text))
    print("전처리 후 글자수:", len(cleaned_text))
    print("청크 수:", len(chunks))

    return chunks


def main():

    pdf_files = list(DATASET_DIR.rglob("*.pdf"))

    print(f"\n총 PDF 개수: {len(pdf_files)}")

    total_chunks = 0

    for pdf in pdf_files:
        chunks = process_pdf(pdf)
        total_chunks += len(chunks)

    print("\n==== 전체 결과 ====")
    print("총 PDF:", len(pdf_files))
    print("총 청크:", total_chunks)


if __name__ == "__main__":
    main()