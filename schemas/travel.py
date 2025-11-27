"""
Travel API Schemas - 여행 플랜 요청/응답 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class TravelPlanRequest(BaseModel):
    """여행 플랜 요청 모델"""
    destination: str = Field(..., description="여행지 (예: 서울, 제주도, 부산)")
    travel_type: str = Field(..., description="여행 타입 (예: 힐링, 음식, 관광, 액티비티)")
    thread_id: Optional[str] = Field(None, description="대화 스레드 ID (멀티 유저 지원)")
    user_id: Optional[str] = Field("anonymous", description="사용자 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "destination": "서울",
                "travel_type": "음식",
                "thread_id": "user-123",
                "user_id": "user-001"
            }
        }


class Place(BaseModel):
    """여행 장소 모델"""
    name: str = Field(..., description="장소 이름")
    category: str = Field(..., description="카테고리 (레스토랑, 관광지, 카페 , 호텔 등)")
    description: str = Field(..., description="장소 설명")
    recommended_duration: str = Field(..., description="추천 체류 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "경복궁",
                "category": "역사유적",
                "description": "조선 왕조의 법궁으로 서울의 대표 관광지",
                "recommended_duration": "2-3시간"
            }
        }


class TravelPlanResponse(BaseModel):
    """여행 플랜 응답 모델"""
    destination: str = Field(..., description="여행지")
    travel_type: str = Field(..., description="여행 타입")
    places: List[Place] = Field(..., description="추천 장소 리스트")
    thread_id: str = Field(..., description="대화 스레드 ID")
    summary: str = Field(..., description="AI가 생성한 여행 계획 요약")

    class Config:
        json_schema_extra = {
            "example": {
                "destination": "서울",
                "travel_type": "음식",
                "places": [
                    {
                        "name": "광장시장",
                        "category": "전통시장",
                        "description": "서울의 대표 전통시장, 빈대떡과 마약김밥이 유명",
                        "recommended_duration": "1-2시간"
                    }
                ],
                "thread_id": "user-123",
                "summary": "서울의 맛있는 음식을 즐길 수 있는 장소들을 추천드립니다."
            }
        }
