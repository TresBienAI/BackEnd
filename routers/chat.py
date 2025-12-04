"""
Chat Router - 대화형 여행 플랜 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, status
from schemas.chat import ChatRequest, ChatResponse
from services.travel_service import TravelPlanService
from typing import Optional

router = APIRouter()

# 서비스 인스턴스 (싱글톤 패턴)
_service: Optional[TravelPlanService] = None


def get_service() -> TravelPlanService:
    """TravelPlanService 싱글톤 인스턴스 가져오기"""
    global _service
    if _service is None:
        _service = TravelPlanService()
    return _service


@router.post("/travel", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_travel(request: ChatRequest):
    """
    대화형 여행 플랜 생성 (Slot Filling)
    
    사용자와 대화를 주고받으며 여행 정보(목적지, 일정, 인원 등)를 수집하고,
    모든 정보가 모이면 여행 계획을 생성합니다.
    """
    try:
        service = get_service()
        result = await service.process_conversation(
            message=request.message,
            thread_id=request.thread_id,
            user_id=request.user_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대화 처리 중 오류 발생: {str(e)}"
        )
