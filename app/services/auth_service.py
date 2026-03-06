import mysql.connector
from app.core.db import get_db_conn
from app.core.security import verify_password


def login_user(username: str, password: str):
    """
    사용자 로그인 인증 처리

    - username 기준으로 사용자 조회
    - 저장된 bcrypt 해시와 입력 비밀번호 비교
    - 인증 성공 시 로그인 로그 기록
    """
    conn = None
    cursor = None

    try:
        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT id, username, password_hash FROM users WHERE username=%s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if not user:
            return {
                "success": False,
                "message": "Invalid credentials",
            }

        if not verify_password(password, user["password_hash"]):
            return {
                "success": False,
                "message": "Invalid credentials",
            }

        try:
            cursor.execute(
                "INSERT INTO login_logs (username, success) VALUES (%s, %s)",
                (username, True),
            )
            conn.commit()
        except mysql.connector.Error:
            pass

        return {
            "success": True,
            "message": "Login successful",
        }

    except mysql.connector.Error as e:
        raise RuntimeError(f"DB error: {str(e)}") from e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()