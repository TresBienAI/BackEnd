"""
사용자 여행 플랜 데이터베이스 모델
"""
from sqlalchemy import Column, String, DateTime, JSON, Text, Index, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class UserTravelPlan(Base):
    """사용자 여행 플랜 저장 테이블"""
    __tablename__ = "user_travel_plans"
    
    # 플랜 고유 ID (UUID)
    plan_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    
    # 사용자 ID (X-User-ID 헤더에서 추출)
    user_id = Column(String(255), nullable=False, index=True)
    
    # 목적지
    destination = Column(String(255), nullable=False)
    
    # 여행 기간 (일수)
    duration_days = Column(Integer, nullable=False)
    
    # 시작 날짜
    start_date = Column(String(50), nullable=True)
    
    # 여행 스타일 (JSON 배열)
    travel_styles = Column(JSON, nullable=False)
    
    # 예산
    budget = Column(String(100), nullable=True)
    
    # 추가 요구사항 (JSON 배열)
    requirements = Column(JSON, nullable=True)
    
    # 전체 플랜 데이터 (JSON - AI가 생성한 일정 전체)
    plan_data = Column(JSON, nullable=False)
    
    # 생성 시간
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 업데이트 시간
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 사용자별 조회를 위한 복합 인덱스
    __table_args__ = (
        Index('idx_user_id_created', 'user_id', 'created_at'),
    )

