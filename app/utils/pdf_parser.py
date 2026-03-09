import fitz
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    text_parts = []

    with fitz.open(path) as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text.strip())

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(f"PDF에서 텍스트를 추출하지 못했습니다: {pdf_path}")

    return full_text