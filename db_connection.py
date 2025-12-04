"""
PostgreSQL 데이터베이스 연결 설정
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 데이터베이스 연결 정보 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True  # 연결 상태 확인
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """데이터베이스 세션 반환"""
    return SessionLocal()

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        session = get_db_session()
        session.execute("SELECT 1")
        session.close()
        print("✅ 데이터베이스 연결 성공!")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return False

