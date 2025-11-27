"""
Travel API Router - 여행 플랜 생성 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from schemas.travel import TravelPlanRequest, TravelPlanResponse
from services.travel_service import TravelPlanService
from typing import Optional

router = APIRouter()

# TravelPlanService 싱글톤 인스턴스
_service: Optional[TravelPlanService] = None


def get_service() -> TravelPlanService:
    """TravelPlanService 싱글톤 인스턴스 가져오기"""
    global _service
    if _service is None:
        _service = TravelPlanService()
    return _service


@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(request: TravelPlanRequest):
    """
    여행 플랜 생성 엔드포인트
    
    - **destination**: 여행지 (예: 서울, 제주도, 부산)
    - **travel_type**: 여행 타입 (예: 힐링, 음식, 관광, 액티비티)
    - **thread_id**: 대화 스레드 ID (선택사항, 멀티 유저 지원)
    - **user_id**: 사용자 ID (선택사항)
    """
    try:
        service = get_service()
        
        result = await service.create_travel_plan(
            destination=request.destination,
            travel_type=request.travel_type,
            thread_id=request.thread_id,
            user_id=request.user_id
        )
        
        return TravelPlanResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"여행 플랜 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/destinations")
async def get_destinations():
    """
    지원하는 여행지 목록 조회
    """
    # MVP에서는 하드코딩
    return {
        "destinations": ["서울", "제주도", "부산"]
    }


@router.get("/types")
async def get_travel_types():
    """
    지원하는 여행 타입 목록 조회
    """
    # MVP에서는 하드코딩
    return {
        "types": ["힐링", "음식", "관광", "액티비티"]
    }
