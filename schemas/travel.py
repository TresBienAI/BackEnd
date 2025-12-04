"""
Travel API Schemas - 여행 플랜 요청/응답 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List


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


