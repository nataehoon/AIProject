from dataclasses import dataclass
from typing import List
import psycopg2

DB_CONFIG = {
    "host":"localhost",
    "port":5432,
    "user":"postgres",
    "password":"",  # trust 모드이므로 빈값 혹은 생략 가능
    "dbname":"postgres"
}

@dataclass
class ChunkedPaperEntity: 
    """PostgreSQL chunked_paper_vectors 테이블 구조와 1:1 매핑되는 POCO 데이터 클래스"""
    title: str
    page_number: int
    paragraph_text: str
    embedding_vector: List[float]

    def to_db_tuple(self):
        cleanned_text = self.paragraph_text.replace("\x00", "")
        cleanned_title = self.title.replace("\x00", "")

        return (
            cleanned_text,
            self.page_number,
            cleanned_title,
            self.embedding_vector
        )

def pad_vector_to_1536(source_vector, target_dim=1536):
    """384차원 오픈소스 벡터 데이터를 테이블 스펙인 1536차원으로 강제 동기화하는 인프라 헬퍼 함수"""
    current_dim = len(source_vector)
    if current_dim >= target_dim:
        return source_vector[:target_dim]

    padding_size = target_dim - current_dim
    return source_vector + [0.0] * padding_size

def bulk_insert_paper_chunks(bulk_data_list: List[ChunkedPaperEntity]):
    """외부 비즈니스 서비스로부터 가공된 데이터 엔티티 컬렉션을 전달받아 일괄 벌크 인서트를 집행하는 함수"""
    if not bulk_data_list:
        print("⚠️ [DB Repository] 인서트할 데이터 큐가 비어있어 가동을 취소합니다.")
        return False

    try:
        # 💡 [버그 전격 저격] C# LINQ의 Select(e => e.ToDbTuple()).ToList() 연산과 완벽히 동치입니다.
        # ChunkedPaperEntity 객체 리스트를 psycopg2 드라이버가 인식할 수 있는 순수 데이터 튜플 리스트로 고속 매핑합니다.
        tuple_data_stream = [entity.to_db_tuple() for entity in bulk_data_list]

        # 단 1번의 커넥션 오픈 세션 파이프라인 형성 (C# using 블록과 동일한 스코프 보호 원리)
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                insert_query = """
                INSERT INTO chunked_paper_vectors (title, page_number, paragraph_text, embedding_vector)
                VALUES (%s, %s, %s, %s);
                """
                # 🔒 1921개의 객체 대신, 정밀 가공된 '순수 튜플 배열'을 바인딩 데이터로 투하합니다.
                print(f"📦 [DB Repository] 단일 배치 트랜잭션 가동 -> {len(tuple_data_stream)}개 데이터 적재 중...")
                cursor.executemany(insert_query, tuple_data_stream)
                
            # 스코프 정상 탈출 시 파이썬 psycopg2 드라이버가 내부적으로 자동 Commit을 집행합니다.
            print(f"💾 [DB Repository] Commit 성료 -> {len(tuple_data_stream)}개 레코드가 물리 디스크 공간에 영구 적재되었습니다.")
            return True
        
    except Exception as e:
        print(f"[DB Repository] 데이터베이스 벌크 인서트 수행 중 치명적 예외 발생 (Rollback): {e}")
        return False