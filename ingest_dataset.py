from pathlib import Path

from app.utils.pdf_parser import extract_text_from_pdf
from app.utils.text_cleaner import clean_text
from app.utils.text_chunker import chunk_text
from app.services.chroma_service import ChromaService


DATASET_DIR = Path("tara_dataset")


def process_pdf(pdf_path: Path):
    print(f"\n===== Processing: {pdf_path.name} =====")

    raw_text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(raw_text)
    chunks = chunk_text(cleaned_text)

    print("chunks:", len(chunks))
    return chunks


def main():
    chroma = ChromaService()
    pdf_files = list(DATASET_DIR.rglob("*.pdf"))

    print("PDF count:", len(pdf_files))

    for pdf in pdf_files:
        source = pdf.stem
        doc_type = pdf.parent.name

        print(f"\n--- {source} ({doc_type}) ---")

        if chroma.document_exists(source):
            print("already ingested -> skip")
            continue

        chunks = process_pdf(pdf)

        if not chunks:
            print("no chunks -> skip")
            continue

        result = chroma.add_documents(chunks, source)

        print("added:", result["added_count"])


if __name__ == "__main__":
    main()