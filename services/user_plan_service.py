"""
사용자 여행 플랜 저장 및 조회 서비스
"""
from sqlalchemy.orm import Session
from models.user_plan import UserTravelPlan
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserPlanService:
    """사용자 여행 플랜 관리 서비스"""
    
    @staticmethod
    def save_plan(
        db_session: Session,
        user_id: str,
        destination: str,
        duration_days: int,
        start_date: str,
        travel_styles: List[str],
        budget: str,
        requirements: List[str],
        plan_data: Dict[str, Any]
    ) -> UserTravelPlan:
        """
        새로운 여행 플랜을 저장합니다.
        
        Args:
            db_session: 데이터베이스 세션
            user_id: 사용자 ID (X-User-ID)
            destination: 여행지
            duration_days: 여행 기간 (일수)
            start_date: 시작 날짜
            travel_styles: 여행 스타일 리스트
            budget: 예산 문자열
            requirements: 추가 요구사항 리스트
            plan_data: AI가 생성한 플랜 데이터 (전체)
        
        Returns:
            저장된 UserTravelPlan 객체
        """
        plan = UserTravelPlan(
            user_id=user_id,
            destination=destination,
            duration_days=duration_days,
            start_date=start_date,
            travel_styles=travel_styles,
            budget=budget,
            requirements=requirements,
            plan_data=plan_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)
        
        return plan
    
    @staticmethod
    def get_plan_by_id(
        db_session: Session,
        plan_id: str,
        user_id: str
    ) -> Optional[UserTravelPlan]:
        """
        플랜 ID로 플랜을 조회합니다.
        (해당 사용자의 플랜만 조회 가능)
        
        Args:
            db_session: 데이터베이스 세션
            plan_id: 플랜 ID
            user_id: 사용자 ID
        
        Returns:
            UserTravelPlan 객체 또는 None
        """
        plan = db_session.query(UserTravelPlan).filter(
            UserTravelPlan.plan_id == plan_id,
            UserTravelPlan.user_id == user_id
        ).first()
        
        return plan
    
    @staticmethod
    def get_user_plans(
        db_session: Session,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[UserTravelPlan], int]:
        """
        사용자의 모든 여행 플랜을 조회합니다. (최신순)
        
        Args:
            db_session: 데이터베이스 세션
            user_id: 사용자 ID
            limit: 조회할 최대 개수
            offset: 오프셋
        
        Returns:
            (플랜 리스트, 전체 개수)
        """
        # 전체 개수 조회
        total_count = db_session.query(UserTravelPlan).filter(
            UserTravelPlan.user_id == user_id
        ).count()
        
        # 페이지네이션으로 조회
        plans = db_session.query(UserTravelPlan).filter(
            UserTravelPlan.user_id == user_id
        ).order_by(UserTravelPlan.created_at.desc()).limit(limit).offset(offset).all()
        
        return plans, total_count
    
    @staticmethod
    def update_plan(
        db_session: Session,
        plan_id: str,
        user_id: str,
        plan_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UserTravelPlan]:
        """
        여행 플랜을 업데이트합니다.
        (해당 사용자의 플랜만 업데이트 가능)
        
        Args:
            db_session: 데이터베이스 세션
            plan_id: 플랜 ID
            user_id: 사용자 ID
            plan_data: 새로운 플랜 데이터
        
        Returns:
            업데이트된 UserTravelPlan 객체 또는 None
        """
        plan = db_session.query(UserTravelPlan).filter(
            UserTravelPlan.plan_id == plan_id,
            UserTravelPlan.user_id == user_id
        ).first()
        
        if not plan:
            return None
        
        if plan_data is not None:
            plan.plan_data = plan_data
        
        plan.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(plan)
        
        return plan
    
    @staticmethod
    def delete_plan(
        db_session: Session,
        plan_id: str,
        user_id: str
    ) -> bool:
        """
        여행 플랜을 삭제합니다.
        (해당 사용자의 플랜만 삭제 가능)
        
        Args:
            db_session: 데이터베이스 세션
            plan_id: 플랜 ID
            user_id: 사용자 ID
        
        Returns:
            성공 여부
        """
        plan = db_session.query(UserTravelPlan).filter(
            UserTravelPlan.plan_id == plan_id,
            UserTravelPlan.user_id == user_id
        ).first()
        
        if not plan:
            return False
        
        db_session.delete(plan)
        db_session.commit()
        
        return True

