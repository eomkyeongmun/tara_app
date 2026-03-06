import mysql.connector
from app.core.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME


def get_db_conn():
    """
    MySQL 데이터베이스 연결을 생성하는 함수

    - 환경 변수에서 로드한 DB 접속 정보를 사용하여
      새로운 MySQL connection 객체를 반환합니다.
    - 서비스 로직에서 DB 연결이 필요할 때 공통적으로 사용됩니다.
    - DB 설정을 config 모듈에서 관리하여 코드와 설정을 분리합니다.

    Returns:
        mysql.connector.connection.MySQLConnection: MySQL 연결 객체
    """
    return mysql.connector.connect(
        host=DB_HOST,        # DB 서버 주소 (ex: localhost / RDS endpoint)
        user=DB_USER,        # DB 접속 계정
        password=DB_PASSWORD, # DB 계정 비밀번호
        database=DB_NAME,    # 사용할 데이터베이스 이름
    )