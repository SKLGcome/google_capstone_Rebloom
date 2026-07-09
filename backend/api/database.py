from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 데이터베이스 파일
DATABASE_URL = "sqlite:///./app.db"

# DB 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# DB 세션 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 모든 모델이 상속받는 Base
Base = declarative_base()