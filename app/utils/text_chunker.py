import re
from typing import List, Dict


MIN_CHUNK_LEN = 120


def is_heading(line: str) -> bool:
    line = line.strip()
    if not line:
        return False

    if len(line) > 80:
        return False

    patterns = [
        r"^\d+(\.\d+)*\s+.+$",                  # 1 제목 / 2.1 제목 / 3.5.2 평가 방식
        r"^\d+(\.\d+)*$",                       # 1 / 1.1 / 2.1.3
        r"^표\s*\d+.*$",                        # 표 8 피해 시나리오 도출
        r"^그림\s*\d+.*$",                      # 그림 3 아이템 정의
        r"^#\d+.*$",                            # #1 CAL(Cybersecurity Assurance Level)
        r"^[가-힣A-Za-z][가-힣A-Za-z0-9\s\-/()]+단계$",
        r"^[가-힣A-Za-z][가-힣A-Za-z0-9\s\-/()]+개요$",
        r"^[가-힣A-Za-z0-9\s\-/()]+:$",
    ]

    return any(re.match(p, line) for p in patterns)


def normalize_lines(text: str) -> List[str]:
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    normalized = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # "1.1" + "배경 및 개요" => "1.1 배경 및 개요"
        if re.match(r"^\d+(\.\d+)*$", line):
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt and len(nxt) <= 60 and not re.match(r"^\d+(\.\d+)*$", nxt):
                    normalized.append(f"{line} {nxt}")
                    i += 2
                    continue

        normalized.append(line)
        i += 1

    return normalized


def split_into_sections(text: str) -> List[Dict[str, str]]:
    lines = normalize_lines(text)

    sections = []
    current_title = ""
    current_body = []

    for line in lines:
        if is_heading(line):
            if current_title or current_body:
                sections.append({
                    "title": current_title.strip(),
                    "body": "\n".join(current_body).strip()
                })
            current_title = line
            current_body = []
        else:
            current_body.append(line)

    if current_title or current_body:
        sections.append({
            "title": current_title.strip(),
            "body": "\n".join(current_body).strip()
        })

    return sections


def split_sentences(text: str) -> List[str]:
    if not text.strip():
        return []

    parts = re.split(
        r"\n+|(?<=[.!?다요음])\s+(?=[가-힣A-Za-z0-9\(\[])",
        text
    )
    return [p.strip() for p in parts if p.strip()]


def split_long_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    results = []
    step = max(1, chunk_size - overlap)

    start = 0
    while start < len(text):
        piece = text[start:start + chunk_size].strip()
        if piece:
            results.append(piece)
        start += step

    return results


def build_chunks_from_section(
    title: str,
    body: str,
    chunk_size: int,
    overlap: int
) -> List[str]:
    if not body.strip():
        return [title] if title and len(title) >= MIN_CHUNK_LEN else []

    sentences = split_sentences(body)
    chunks = []
    current = title.strip() if title else ""

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        candidate = f"{current}\n{sent}".strip() if current else sent

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current and len(current) >= MIN_CHUNK_LEN:
            chunks.append(current)

        if len(sent) > chunk_size:
            parts = split_long_text(sent, chunk_size=chunk_size, overlap=overlap)
            for part in parts:
                piece = f"{title}\n{part}".strip() if title else part
                if len(piece) >= MIN_CHUNK_LEN:
                    chunks.append(piece)
            current = title.strip() if title else ""
        else:
            current = f"{title}\n{sent}".strip() if title else sent

    if current and len(current) >= MIN_CHUNK_LEN:
        chunks.append(current)

    return chunks


def merge_short_chunks(chunks: List[str], min_len: int = MIN_CHUNK_LEN) -> List[str]:
    if not chunks:
        return []

    merged = []
    buffer = ""

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        if len(chunk) < min_len:
            buffer = f"{buffer}\n{chunk}".strip() if buffer else chunk
            continue

        if buffer:
            chunk = f"{buffer}\n{chunk}".strip()
            buffer = ""

        merged.append(chunk)

    if buffer:
        if merged:
            merged[-1] = f"{merged[-1]}\n{buffer}".strip()
        else:
            merged.append(buffer)

    return merged


def chunk_text(text: str, chunk_size: int = 550, overlap: int = 80) -> List[str]:
    if not text or not text.strip():
        return []

    sections = split_into_sections(text)

    all_chunks = []
    for section in sections:
        title = section["title"]
        body = section["body"]

        section_chunks = build_chunks_from_section(
            title=title,
            body=body,
            chunk_size=chunk_size,
            overlap=overlap
        )
        all_chunks.extend(section_chunks)

    all_chunks = merge_short_chunks(all_chunks, min_len=MIN_CHUNK_LEN)
    return all_chunks