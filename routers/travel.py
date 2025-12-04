"""
Travel API Router - 여행 플랜 생성 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from tools.travel_tools import generate_travel_itinerary


class TravelPlanRequest(BaseModel):
    """여행 계획 생성 요청"""
    destination: str
    start_date: str  # 출발 날짜 (예: "2025-12-15")
    travel_styles: List[str]
    duration_days: int
    budget: str
    requirements: List[str] = []
    budget_level: Optional[int] = None
    include_debug: bool = True  # 기본값을 True로 변경 (점수/클러스터링 포함)


def calculate_budget_level(budget_str: str, duration_days: int) -> int:
    """
    여행 기간과 예산 문자열을 기반으로 price_level 계산
    
    Args:
        budget_str: 예산 문자열 (예: "50만원", "100만원")
        duration_days: 여행 기간 (일수)
    
    Returns:
        price_level: 
            1 - 1만원 미만 (저가)
            2 - 1만원 ~ 3만원 (저~중가)
            3 - 4만원 ~ 10만원 미만 (중가)
            4 - 10만원 이상 (고급)
    
    예시:
        - 1일, 5만원 → level 1 (일인당 5,000원)
        - 4일, 80만원 → level 2 (일인당 20,000원)
        - 4일, 200만원 → level 3 (일인당 50,000원)
        - 4일, 500만원 → level 4 (일인당 125,000원)
    """
    try:
        # 예산 문자열에서 숫자와 "만원"/"억원" 파싱
        # "50만원" → 50 * 10000 = 500000
        # "100만원" → 100 * 10000 = 1000000
        # "1억원" → 1 * 100000000 = 100000000
        
        budget_str = budget_str.strip()
        
        # 숫자 부분 추출
        import re
        numbers = re.findall(r'\d+', budget_str)
        if not numbers:
            return 2
        
        budget_num = int(numbers[0])  # 첫 번째 숫자만 추출
        
        # 단위 확인
        if '억' in budget_str:
            budget_num *= 100000000
        elif '만' in budget_str:
            budget_num *= 10000
        else:
            # 단위 없으면 원 단위로 간주
            pass
        
        # 기준: 1인 1일 기준으로 계산
        budget_per_day = budget_num / duration_days if duration_days > 0 else budget_num
        
        # price_level 결정 (1인 1일 기준, 단위: 원)
        if budget_per_day < 10000:
            # 1만원 미만
            return 1
        elif budget_per_day <= 30000:
            # 1만원 ~ 3만원
            return 2
        elif budget_per_day < 100000:
            # 4만원 ~ 10만원 미만
            return 3
        else:
            # 10만원 이상
            return 4
    except:
        # 파싱 실패 시 보통 레벨 (2) 반환
        return 2


router = APIRouter()


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


@router.post("/plans")
async def create_itinerary_json(request: TravelPlanRequest):
    """
    여행 일정을 JSON 형식으로 반환 (프론트엔드용)
    
    - **destination**: 여행지 (예: 서울, 제주도, 부산)
    - **travel_styles**: 여행 스타일 리스트 (예: ["로맨틱한 장소", "맛집 투어"])
    - **duration_days**: 여행 기간 (일수)
    - **budget**: 예산 (예: "50만원", "100만원")
    - **requirements**: 추가 요구사항 (예: ["임신", "적게 걷기"])
    - **budget_level**: (선택) 직접 지정할 예산 등급. 미지정 시 자동 계산
    - **include_debug**: (선택) True면 상세한 디버그 정보 포함 (클러스터링, 점수 등)
    
    Budget Level 기준 (일인 1일):
    - level 1: 5만원 이하 (저렴)
    - level 2: 5만원~15만원 (보통)
    - level 3: 15만원 이상 (고급)
    
    응답:
    - destination: 여행지
    - duration_days: 여행 기간
    - total_places: 선택된 총 장소 수
    - itinerary: 날짜별 일정 (각 날짜마다 schedule, summary 포함)
    - debug_info: (include_debug=true일 때만) 상세 정보
    """
    try:
        # budget_level이 미지정되면 자동으로 계산
        budget_level = request.budget_level
        if budget_level is None:
            budget_level = calculate_budget_level(request.budget, request.duration_days)
        
        result = generate_travel_itinerary.invoke({
            "destination": request.destination,
            "travel_styles": request.travel_styles,
            "duration_days": request.duration_days,
            "requirements": request.requirements,
            "budget_level": budget_level,
            "include_debug": request.include_debug
        })
        
        # 결과가 Dict인지 확인하고 정렬해서 반환
        if isinstance(result, dict):
            return {
                "success": True,
                "data": result,
                "message": "여행 일정이 성공적으로 생성되었습니다."
            }
        else:
            # 예상치 못한 형식이면 에러 처리
            return {
                "success": False,
                "error": f"예상치 못한 응답 형식: {type(result)}",
                "data": result
            }
    except Exception as e:
        import traceback
        print(f"Error in /travel/plans: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"일정 생성 중 오류 발생: {str(e)}"
        )


class UpdateHotelRequest(BaseModel):
    """호텔 변경 요청"""
    destination: str
    travel_styles: list[str]
    duration_days: int
    budget: str
    selected_places: list[dict]
    new_hotel: dict
    requirements: list[str] = []
    budget_level: Optional[int] = None

@router.post("/plans/update-hotel")
async def update_hotel_and_recalculate(request: UpdateHotelRequest):
    """
    선택된 호텔을 변경하고 일정을 재계산
    
    ⭐ 중요: 선택된 장소들(selected_places)은 유지되고, 
       호텔만 변경되어 이동 거리/시간과 최적 경로만 재계산됩니다.
    
    - **destination**: 여행지
    - **travel_styles**: 여행 스타일
    - **duration_days**: 여행 기간
    - **budget**: 예산
    - **selected_places**: 유지할 장소들 (호텔 변경 후에도 이 장소들은 변경 안 됨)
    - **new_hotel**: 새로운 호텔 정보 (name, latitude, longitude 포함)
    - **requirements**: 추가 요구사항
    - **budget_level**: 예산 등급
    
    응답:
    - 선택된 장소들은 유지됨 ✅
    - 새 호텔을 기준으로 재계산된 일정
    - 각 장소까지의 이동 거리/시간 업데이트 (새 호텔 기준)
    - 최적 경로 재계산 (새 호텔 기준)
    
    예시:
    기존: 롯데 호텔 → 경복궁 → 명동 → 롯데 호텔
    변경: 신라 호텔 → 경복궁 → 명동 → 신라 호텔
    (경복궁, 명동은 유지 + 거리/시간만 재계산)
    """
    try:
        from services.itinerary_service import ItineraryService
        
        budget_level = request.budget_level
        if budget_level is None:
            budget_level = calculate_budget_level(request.budget, request.duration_days)
        
        # 이동 거리/시간 재계산 (선택된 장소는 유지)
        itinerary_service = ItineraryService()
        
        # ⭐ selected_places의 장소들은 변경되지 않음
        # 새 호텔만 기준점으로 사용해서 거리/시간/경로만 재계산
        recalculated_itinerary = await itinerary_service.create_itinerary_async(
            places=request.selected_places,  # 선택된 장소들 유지 ✅
            duration_days=request.duration_days,
            alternative_places=[]
        )
        
        return {
            "destination": request.destination,
            "duration_days": request.duration_days,
            "total_places": len(request.selected_places),
            "hotel": request.new_hotel,
            "itinerary": recalculated_itinerary,
            "message": "호텔이 변경되었으며, 선택된 장소들은 유지되고 이동 경로만 재계산되었습니다."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일정 재계산 중 오류 발생: {str(e)}"
        )


class ReplacePlaceRequest(BaseModel):
    """장소 교체 요청"""
    day: int
    old_place: dict
    new_place: dict
    all_places: list[dict]
    duration_days: int

@router.post("/plans/replace-place")
async def replace_place_and_recalculate(request: ReplacePlaceRequest):
    """
    특정 날짜의 장소를 다른 장소로 교체하고 일정을 재계산
    
    ⭐ 기능:
    - 특정 Day의 특정 장소를 새로운 장소로 교체
    - 그 Day의 전체 일정 재계산 (거리/시간/경로)
    - 다른 Day는 영향 없음
    
    - **day**: 변경할 날짜 (1, 2, 3, ...)
    - **old_place**: 제거할 장소 정보
    - **new_place**: 새로운 장소 정보 (name, latitude, longitude, type 포함)
    - **all_places**: 현재 선택된 모든 장소들
    - **duration_days**: 전체 여행 기간
    
    응답:
    - 해당 Day만 재계산된 일정
    - 이동 거리/시간 업데이트
    - 최적 경로 재계산
    
    예시:
    Day 2의 명동을 동대문으로 변경
    기존 Day 2: 숙소 → 경복궁 → 명동 → 남산타워 → 숙소
    변경 Day 2: 숙소 → 경복궁 → 동대문 → 남산타워 → 숙소
    """
    try:
        from services.itinerary_service import ItineraryService
        
        # 장소 교체 (old_place 제거, new_place 추가)
        updated_places = []
        for place in request.all_places:
            if place.get('name') == request.old_place.get('name') and place.get('latitude') == request.old_place.get('latitude'):
                # 해당 장소를 새로운 장소로 교체
                updated_places.append(request.new_place)
            else:
                updated_places.append(place)
        
        # 전체 일정 재계산
        itinerary_service = ItineraryService()
        recalculated_itinerary = await itinerary_service.create_itinerary_async(
            places=updated_places,
            duration_days=request.duration_days,
            alternative_places=[]
        )
        
        # 해당 Day만 응답
        day_schedule = None
        if request.day <= len(recalculated_itinerary):
            day_schedule = recalculated_itinerary[request.day - 1]
        
        return {
            "day": request.day,
            "old_place": request.old_place,
            "new_place": request.new_place,
            "day_schedule": day_schedule,
            "message": f"Day {request.day}의 장소가 변경되었으며, 해당 날짜 일정이 재계산되었습니다.",
            "updated_itinerary": recalculated_itinerary
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"장소 교체 중 오류 발생: {str(e)}"
        )
