"""
Travel Tools - 여행지 검색 및 필터링 LangGraph 툴
"""
from langchain_core.tools import tool
from typing import List, Dict, Any
import asyncio
from services.search_service import SearchService
from services.itinerary_service import ItineraryService

search_service = SearchService()
itinerary_service = ItineraryService()


# MVP용 샘플 데이터 (하드코딩)
SAMPLE_PLACES = {
    "서울": {
        "음식": [
            {
                "name": "광장시장",
                "category": "전통시장",
                "description": "서울의 대표 전통시장, 빈대떡과 마약김밥이 유명",
                "recommended_duration": "1-2시간"
            },
            {
                "name": "이태원 맛집거리",
                "category": "레스토랑거리",
                "description": "다양한 세계 음식을 맛볼 수 있는 이태원",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "망원동 카페거리",
                "category": "카페거리",
                "description": "감성 넘치는 카페들이 즐비한 망원동",
                "recommended_duration": "1-2시간"
            }
        ],
        "관광": [
            {
                "name": "경복궁",
                "category": "역사유적",
                "description": "조선 왕조의 법궁으로 서울의 대표 관광지",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "남산타워",
                "category": "전망대",
                "description": "서울의 야경을 한눈에 볼 수 있는 남산타워",
                "recommended_duration": "1-2시간"
            },
            {
                "name": "북촌 한옥마을",
                "category": "문화유산",
                "description": "전통 한옥이 보존된 아름다운 마을",
                "recommended_duration": "1-2시간"
            }
        ],
        "힐링": [
            {
                "name": "한강공원",
                "category": "공원",
                "description": "서울 시민들의 휴식 공간, 자전거와 피크닉 명소",
                "recommended_duration": "2-4시간"
            },
            {
                "name": "서울숲",
                "category": "공원",
                "description": "도심 속 자연을 만끽할 수 있는 대형 공원",
                "recommended_duration": "2-3시간"
            }
        ],
        "액티비티": [
            {
                "name": "롯데월드",
                "category": "테마파크",
                "description": "실내외 놀이기구를 즐길 수 있는 테마파크",
                "recommended_duration": "4-6시간"
            },
            {
                "name": "한강 수상레저",
                "category": "수상스포츠",
                "description": "카약, 패들보드 등 다양한 수상 액티비티",
                "recommended_duration": "2-3시간"
            }
        ]
    },
    "제주도": {
        "힐링": [
            {
                "name": "협재 해수욕장",
                "category": "해변",
                "description": "에메랄드빛 바다와 고운 모래가 아름다운 해변",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "한라산 둘레길",
                "category": "트레킹",
                "description": "제주의 자연을 느끼며 걸을 수 있는 숲길",
                "recommended_duration": "3-4시간"
            },
            {
                "name": "곽지과물",
                "category": "카페",
                "description": "바다 전망이 아름다운 제주 감성 카페",
                "recommended_duration": "1-2시간"
            }
        ],
        "음식": [
            {
                "name": "동문시장",
                "category": "전통시장",
                "description": "제주 토속 음식과 해산물을 맛볼 수 있는 시장",
                "recommended_duration": "1-2시간"
            },
            {
                "name": "흑돼지거리",
                "category": "음식거리",
                "description": "제주 대표 음식인 흑돼지 구이를 맛볼 수 있는 거리",
                "recommended_duration": "1-2시간"
            }
        ],
        "관광": [
            {
                "name": "성산일출봉",
                "category": "자연경관",
                "description": "UNESCO 세계자연유산, 일출 명소",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "우도",
                "category": "섬",
                "description": "제주 옆 작은 섬, 자전거 투어 명소",
                "recommended_duration": "4-5시간"
            }
        ],
        "액티비티": [
            {
                "name": "제주 올레길",
                "category": "트레킹",
                "description": "제주 해안을 따라 걷는 26개 코스",
                "recommended_duration": "4-6시간"
            },
            {
                "name": "스쿠버다이빙",
                "category": "수상스포츠",
                "description": "제주 바다 속 세상을 탐험",
                "recommended_duration": "2-3시간"
            }
        ]
    },
    "부산": {
        "관광": [
            {
                "name": "해운대 해수욕장",
                "category": "해변",
                "description": "한국 최고의 해수욕장, 백사장과 야경이 아름다움",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "감천 문화마을",
                "category": "문화관광",
                "description": "알록달록한 집들이 모여있는 예술 마을",
                "recommended_duration": "2-3시간"
            }
        ],
        "음식": [
            {
                "name": "자갈치 시장",
                "category": "전통시장",
                "description": "한국 최대 수산시장, 신선한 해산물",
                "recommended_duration": "1-2시간"
            },
            {
                "name": "광안리 횟집거리",
                "category": "음식거리",
                "description": "신선한 회와 바다 전망을 함께 즐기는 거리",
                "recommended_duration": "2-3시간"
            }
        ],
        "힐링": [
            {
                "name": "태종대",
                "category": "자연경관",
                "description": "절벽과 바다가 어우러진 부산의 명소",
                "recommended_duration": "2-3시간"
            },
            {
                "name": "이기대 해안산책로",
                "category": "산책로",
                "description": "바다를 보며 걷는 아름다운 산책로",
                "recommended_duration": "2-3시간"
            }
        ]
    }
}


@tool
async def search_places(destination: str, travel_type: str) -> List[Dict[str, Any]]:
    """
    여행지와 여행 타입에 맞는 장소를 검색하는 툴
    
    Args:
        destination: 여행지 (예: 서울, 제주도, 부산)
        travel_type: 여행 타입 (예: 힐링, 음식, 관광, 액티비티)
    
    Returns:
        장소 리스트 (각 장소는 name, category, description, recommended_duration 포함)
    """
    print(f"--- [Tool] search_places 호출됨: {destination} - {travel_type} ---")
    await asyncio.sleep(0.1)  # 비동기 시뮬레이션
    
    # 여행지가 데이터에 없는 경우
    if destination not in SAMPLE_PLACES:
        return []
    
    # 여행 타입이 없는 경우
    if travel_type not in SAMPLE_PLACES[destination]:
        return []
    
    return SAMPLE_PLACES[destination][travel_type]


@tool
async def filter_by_type(places: List[Dict[str, Any]], travel_type: str) -> List[Dict[str, Any]]:
    """
    검색된 장소들을 여행 타입에 따라 필터링하는 툴
    
    Args:
        places: 장소 리스트
        travel_type: 여행 타입
    
    Returns:
        필터링된 장소 리스트
    """
    print(f"--- [Tool] filter_by_type 호출됨: {travel_type} ---")
    await asyncio.sleep(0.1)
    
    # MVP에서는 단순히 places를 그대로 반환 (이미 검색 시 필터링됨)
    # 향후 확장 시 카테고리별 정렬, 우선순위 조정 등 추가 가능
    return places


@tool
async def get_supported_destinations() -> List[str]:
    """
    지원하는 여행지 목록을 반환하는 툴
    
    Returns:
        지원하는 여행지 리스트
    """
    print("--- [Tool] get_supported_destinations 호출됨 ---")
    await asyncio.sleep(0.1)
    return list(SAMPLE_PLACES.keys())


@tool
async def get_supported_types(destination: str) -> List[str]:
    """
    특정 여행지에서 지원하는 여행 타입 목록을 반환하는 툴
    
    Args:
        destination: 여행지
    
    Returns:
        지원하는 여행 타입 리스트
    """
    print(f"--- [Tool] get_supported_types 호출됨: {destination} ---")
    await asyncio.sleep(0.1)
    
    if destination not in SAMPLE_PLACES:
        return []
    
    return list(SAMPLE_PLACES[destination].keys())

async def _generate_travel_itinerary_async(
    destination: str,
    travel_styles: List[str], 
    duration_days: int, 
    requirements: List[str] =[], 
    budget_level: int = 2,
    include_debug: bool = False
) -> Dict[str,Any]:
    """
    비동기 여행 일정 생성 (거리 계산 병렬 처리)
    """
    print(f"--- [Tool] 일정 생성 시작 : {destination} ({duration_days}일) ---")

    #1. 장소 검색
    candidates = search_service.search_places_with_priority(
        destination=destination,
        travel_styles=travel_styles,
        requirements=requirements,
        price_level=budget_level,
    )

    if not candidates:
        return {"error" : "조건에 맞는 장소를 찾을 수 없습니다."}
    
    print(f"--- [Tool] 검색된 장소 : {len(candidates)}개 ---")

    #2. 일정 생성 (비동기)
    max_places = duration_days *5
    selected_places = candidates[:max_places]
    
    # 예비 장소 (사용하지 않은 상위 장소들)
    alternative_places = candidates[max_places:max_places + 20]  # 추가로 20개

    itinerary = await itinerary_service.create_itinerary_async(
        places = selected_places, 
        duration_days=duration_days,
        alternative_places=alternative_places,
        include_debug_info=include_debug
    )

    # include_debug=True인 경우 클러스터링 정보 추출
    clustering_info = None
    final_itinerary = itinerary if not include_debug else itinerary.get("itinerary", itinerary)
    
    if include_debug and isinstance(final_itinerary, list) and len(final_itinerary) > 0:
        # 첫 날에서 클러스터링 정보 추출
        if "clustering_debug_info" in final_itinerary[0]:
            clustering_info = final_itinerary[0].pop("clustering_debug_info")
    
    response = {
        "destination" : destination,
        "duration_days": duration_days,
        "total_places": len(selected_places),
        "itinerary": final_itinerary
    }
    
    # include_debug=True인 경우 상세 정보 추가
    if include_debug:
        response["debug_info"] = {
            "total_searched_places": len(candidates),
            "selected_places_count": len(selected_places),
            "alternative_places_count": len(alternative_places),
            "selected_places": [
                {
                    "name": p.get("name"),
                    "type": p.get("type"),
                    "score": p.get("score"),
                    "latitude": p.get("latitude"),
                    "longitude": p.get("longitude"),
                    "price_level": p.get("price_level")
                }
                for p in selected_places
            ],
            "alternative_places": [
                {
                    "name": p.get("name"),
                    "type": p.get("type"),
                    "score": p.get("score"),
                    "latitude": p.get("latitude"),
                    "longitude": p.get("longitude")
                }
                for p in alternative_places
            ],
            "clustering": clustering_info
        }
    
    return response


@tool
def generate_travel_itinerary(
    destination: str,
    travel_styles: List[str], 
    duration_days: int, 
    requirements: List[str] =[], 
    budget_level: int = 2,
    include_debug: bool = True
) -> Dict[str,Any]:
    """
    여행 정보를 바탕으로 최적의 여행 일정을 생성하는 도구.
    
    내부적으로 비동기 처리를 사용하여 거리 계산을 병렬화
    
    Args:
        include_debug: True(기본)이면 점수, 클러스터링 정보 등 상세 정보 포함
                      False로 설정하면 기본 일정만 반환 (응답 크기 최소화)
    """
    import asyncio
    import concurrent.futures
    import threading
    
    # 비동기 함수를 동기로 실행하는 헬퍼
    def run_async_in_thread():
        """스레드에서 비동기 함수 실행"""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(
                _generate_travel_itinerary_async(
                    destination, travel_styles, duration_days, requirements, budget_level, include_debug
                )
            )
        finally:
            new_loop.close()
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # ✅ 이미 실행 중인 루프가 있으면 스레드에서 실행
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_async_in_thread)
                return future.result()
        else:
            # 루프가 실행 중이 아니면 현재 루프 사용
            return loop.run_until_complete(
                _generate_travel_itinerary_async(
                    destination, travel_styles, duration_days, requirements, budget_level, include_debug
                )
            )
    except RuntimeError:
        # 루프가 없으면 새로 만들어서 실행
        return asyncio.run(
            _generate_travel_itinerary_async(
                destination, travel_styles, duration_days, requirements, budget_level, include_debug
            )
        )







# 모든 툴을 리스트로 export
travel_tools = [
    search_places,
    filter_by_type,
    get_supported_destinations,
    get_supported_types,
    generate_travel_itinerary
]