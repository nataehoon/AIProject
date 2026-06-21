import psycopg2
from pgvector.psycopg2 import register_vector

def init_database():
    try:
        # 1. 외장 SSD 포터블 PostgreSQL 연결 설정
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="",  # trust 모드이므로 빈값 혹은 생략 가능
            dbname="postgres"
        )
        # 자동 커밋 설정 (CREATE EXTENSION 등은 트랜잭션 블록 외에서 실행되어야 함)
        conn.autocommit = True
        cursor = conn.cursor()

        print("🟢 PostgreSQL 서버 연결 성공!")

        # 2. pgvector 확장 기능 활성화 (최초 1회 필수)
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("🟢 pgvector 확장 기능 활성화 완료!")

        # 3. 잘 설치되었는지 버전 확인 테스트
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        print(f"🎉 설치된 pgvector 버전: {version[0]}")

        # 연결 종료
        cursor.close()
        conn.close()
        print("🟢 테스트 및 세팅 정상 종료.")

    except Exception as e:
        print(f"❌ DB 연동 실패! 에러 내용: {e}")

if __name__ == "__main__":
    init_database()