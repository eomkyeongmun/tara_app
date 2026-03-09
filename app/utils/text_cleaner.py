import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # CONTENTS 제거
    text = re.sub(r"(?im)^\s*CONTENTS\s*$", "", text)

    # dot leader 제거
    text = re.sub(r"·{3,}\s*\d+\s*", "\n", text)

    # 반복 헤더/푸터 제거
    text = re.sub(r"(?m)^\s*\d+\.\s*[^\n]{0,80}?\s+\d+\s*$", "", text)
    text = re.sub(r"(?m)^\s*별첨\s+\d+\s*$", "", text)

    # 장식용 01, 02, 03 제거
    text = re.sub(r"(?m)^\s*0\d\s*$", "", text)

    # 단독 페이지 번호 제거
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # 하이픈 줄바꿈 복원
    text = re.sub(r"(?<=[가-힣A-Za-z])-\n(?=[가-힣A-Za-z])", "", text)

    # 문장 중간 강제 줄바꿈 완화
    text = re.sub(r"(?<=[가-힣A-Za-z])\n(?=[가-힣A-Za-z])", " ", text)

    # 공백 정리
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()