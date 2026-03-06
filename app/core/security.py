import bcrypt


def hash_password(password: str) -> str:
    """
    평문 비밀번호를 bcrypt 해시 문자열로 변환한다.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    입력 비밀번호와 저장된 bcrypt 해시를 비교한다.
    """
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )