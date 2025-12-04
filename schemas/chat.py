"""
Chat API Schemas - 대화형 여행 플랜 요청/응답 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str = Field(..., description="사용자 메시지")
    thread_id: Optional[str] = Field(None, description="대화 스레드 ID (세션 유지용)")
    user_id: Optional[str] = Field("anonymous", description="사용자 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "서울 여행 가고 싶어",
                "thread_id": "user-123",
                "user_id": "user-001"
            }
        }


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str = Field(..., description="AI 응답 메시지 (질문 또는 계획)")
    thread_id: str = Field(..., description="대화 스레드 ID")
    is_completed: bool = Field(False, description="여행 계획 생성 완료 여부 (deprecated: plan_done 사용)")
    plan_done: bool = Field(False, description="여행 계획 생성 완료 여부")
    plan_data: Optional[Dict[str, Any]] = Field(None, description="완성된 여행 일정 JSON 데이터 (plan_done=true일 때만 포함)")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "좋은 선택입니다! 여행 계획을 생성했습니다.",
                "thread_id": "user-123",
                "is_completed": True,
                "plan_done": True,
                "plan_data": {
                    "destination": "서울",
                    "duration_days": 3,
                    "total_places": 15,
                    "itinerary": [
                        {
                            "day": 1,
                            "schedule": [
                                {
                                    "order": 1,
                                    "time_slot": "morning",
                                    "start_time": "09:00",
                                    "place": {"name": "경복궁"}
                                }
                            ]
                        }
                    ]
                }
            }
        }
