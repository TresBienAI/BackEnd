import asyncio
from typing import List, Dict, Any
from services.route_optimizer import RouteOptimizer


class ItineraryService:
    def __init__(self):
        self.optimizer = RouteOptimizer()
    
    async def create_itinerary_async(
        self,
        places: List[dict],
        duration_days: int,
        alternative_places: List[dict] = [],
        include_debug_info: bool = False
    ) -> Any:
        """
        비동기 날짜별 여행 일정 생성
        
        거리 계산을 병렬로 처리하여 성능 향상
        
        Args:
            include_debug_info: True면 상세한 디버그 정보 포함
        """
        result = await self._create_itinerary_impl(places, duration_days, alternative_places)
        
        if include_debug_info:
            return {
                "itinerary": result,
                "debug_info": {
                    "total_selected_places": len(places),
                    "clustering": self.clustered_places if hasattr(self, 'clustered_places') else None,
                    "all_places_with_scores": places
                }
            }
        
        return result
    
    def create_itinerary(
        self,
        places: List[dict],
        duration_days: int,
        alternative_places: List[dict] = [],
        include_debug_info: bool = False
    ) -> Any:
        """
        날짜별 여행 일정 생성 (동기 버전)
        
        기존 코드와의 호환성을 위해 유지
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 새 루프 생성
                new_loop = asyncio.new_event_loop()
                result = new_loop.run_until_complete(
                    self._create_itinerary_impl(places, duration_days, alternative_places)
                )
            else:
                result = loop.run_until_complete(
                    self._create_itinerary_impl(places, duration_days, alternative_places)
                )
        except RuntimeError:
            # 새로운 루프 생성
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(
                self._create_itinerary_impl(places, duration_days, alternative_places)
            )
        
        if include_debug_info:
            return {
                "itinerary": result,
                "debug_info": {
                    "total_selected_places": len(places),
                    "clustering": self.clustered_places if hasattr(self, 'clustered_places') else None,
                    "all_places_with_scores": places
                }
            }
        
        return result
    
    async def _create_itinerary_impl(
        self,
        places: List[dict],
        duration_days: int,
        alternative_places: List[dict] = []
    ) -> List[Dict]:
        """
        실제 일정 생성 로직 (비동기)
        """

        # 1. 장소 타입별 분류
        # DB의 main_type: 관광지, 음식점, 숙박, 문화시설, 쇼핑, 레저스포츠
        # 기존 타입: activity, restaurant, cafe, hotel, museum, shopping
        activities = [p for p in places if p['type'] in ['activity', 'museum', 'shopping', '관광지', '문화시설', '레저스포츠']]
        restaurants = [p for p in places if p['type'] in ['restaurant', '음식점']]
        cafes = [p for p in places if p['type'] == 'cafe']    
        hotels = [p for p in places if p['type'] in ['hotel', '숙박']]

        itinerary = []
        clustering_debug_info = None  # 클러스터링 정보 저장용

        # 호텔은 점수 높은 순으로 정렬 (메인 숙소 선정용)
        hotels.sort(key=lambda x: x.get('score', 0), reverse=True)
        main_hotel = hotels[0] if hotels else None

        for day in range(1, duration_days + 1):
            day_plan = {
                "day": day,
                "schedule": [],
                "summary": {}
            }

            # 하루 일정 구성 로직 (클러스터링 적용)
            
            # 1. 전체 장소 리스트 준비 (첫 날에만 실행)
            if day == 1:
                all_places_to_visit = []
                # 비율에 맞춰 장소 혼합 (Activity 2 : Restaurant 2 : Cafe 1)
                while activities or restaurants or cafes:
                    if activities: all_places_to_visit.append(activities.pop(0))
                    if restaurants: all_places_to_visit.append(restaurants.pop(0))
                    if activities: all_places_to_visit.append(activities.pop(0))
                    if cafes: all_places_to_visit.append(cafes.pop(0))
                    if restaurants: all_places_to_visit.append(restaurants.pop(0))
                
                # 2. 일자별로 클러스터링 (K-Means)
                self.clustered_places = self.optimizer.cluster_places(all_places_to_visit, duration_days)
                
                # 클러스터링 정보 저장 (나중에 반환할 때 사용)
                clustering_debug_info = {
                    "clustering_method": "K-Means",
                    "total_places_for_clustering": len(all_places_to_visit),
                    "num_clusters": duration_days,
                    "clusters": [
                        {
                            "day": i + 1,
                            "places_in_cluster": len(self.clustered_places[i]),
                            "cluster_places": [
                                {
                                    "name": p.get("name"),
                                    "type": p.get("type"),
                                    "score": p.get("score"),
                                    "latitude": p.get("latitude"),
                                    "longitude": p.get("longitude")
                                }
                                for p in self.clustered_places[i]
                            ]
                        }
                        for i in range(len(self.clustered_places))
                    ]
                }

            # 3. 해당 일자의 클러스터 가져오기
            daily_places = self.clustered_places[day-1] if day <= len(self.clustered_places) else []

            # 해당 일자의 경로 최적화
            # 숙소가 있으면: 모든 날(1일차 포함)을 숙소를 기준으로 시작
            # 숙소가 없으면: 시작점 없음 (None)

            start_loc = main_hotel if main_hotel else None
            optimized_places = self.optimizer.optimize_route(daily_places, start_location=start_loc)

            # 마지막에 숙소 추가(마지막 날 제외)
            if main_hotel and day < duration_days:
                optimized_places.append(main_hotel)

            # 시간표 생성 (09:00 시작)
            current_time_min = 9*60
            total_dist = 0
            total_time = 0

            # 모든 거리 계산을 준비 (병렬 처리 위함)
            distance_tasks = []
            for i, place in enumerate(optimized_places):
                if i > 0:
                    prev_place = optimized_places[i-1]
                    lat1 = prev_place.get('latitude', 0)
                    lon1 = prev_place.get('longitude', 0)
                    lat2 = place.get('latitude', 0)
                    lon2 = place.get('longitude', 0)
                    
                    straight_dist = self.optimizer.get_straight_distance(lat1, lon1, lat2, lon2)
                    mode = "walk" if straight_dist < 1.5 else "public"
                    
                    # 기본값은 walk로 비동기 거리 계산
                    # (추후 public도 선택 옵션으로 제공하므로 walk만 기본값으로)
                    task = self.optimizer.calculate_distance_async(
                        lat1, lon1, lat2, lon2,
                        mode="walk"  # 기본값: walk
                    )
                    distance_tasks.append((i, "walk", task))
            
            # 모든 거리를 병렬로 계산
            if distance_tasks:
                travel_results = await asyncio.gather(
                    *[task for _, _, task in distance_tasks],
                    return_exceptions=False
                )
            else:
                travel_results = []

            # 거리 계산 결과를 schedule_item에 반영
            travel_result_map = {}
            for idx, (i, mode, _) in enumerate(distance_tasks):
                travel_result_map[i] = (travel_results[idx], mode)

            # 일정 생성
            for i, place in enumerate(optimized_places):
                travel_info = None
                travel_options = None
                
                if i > 0 and i in travel_result_map:
                    travel_result, mode = travel_result_map[i]
                    dist = travel_result["distance_km"]
                    travel_time = travel_result["time_minutes"]

                    current_time_min += travel_time
                    total_dist += dist
                    total_time += travel_time

                    # 현재 선택된 교통수단
                    travel_info = {
                        "distance_km": dist,
                        "time_minutes": travel_time,
                        "mode": mode,
                        "description": f"이동 {travel_time}분 ({dist}km)",
                        "method": travel_result.get("method", "unknown")
                    }
                    
                    # 모든 교통수단 선택지 제공
                    if i > 0:
                        prev_place = optimized_places[i-1]
                        lat1 = prev_place.get('latitude', 0)
                        lon1 = prev_place.get('longitude', 0)
                        lat2 = place.get('latitude', 0)
                        lon2 = place.get('longitude', 0)
                        
                        travel_options = {}
                        
                        # 각 교통수단별 거리/시간 계산 (걷기, 차량, 대중교통)
                        for transport_mode in ["walk", "public"]:  # walk와 public만 제공
                            transport_result = self.optimizer.calculate_distance(
                                lat1, lon1, lat2, lon2,
                                mode=transport_mode
                            )
                            
                            travel_options[transport_mode] = {
                                "distance_km": transport_result["distance_km"],
                                "time_minutes": transport_result["time_minutes"],
                                "mode": transport_mode,
                                "description": f"{transport_mode} - {transport_result['time_minutes']}분 ({transport_result['distance_km']}km)",
                                "method": transport_result.get("method", "unknown")
                            }
                        
                        # 기본값은 walk로 설정 (travel_info에 walk 사용)
                        travel_info = travel_options.get("walk", travel_info)

                # 체류 시간 (기본 90분)
                duration_min = 90
                start_time_str = f"{current_time_min // 60:02d}:{current_time_min % 60:02d}"
                current_time_min += duration_min
                end_time_str = f"{current_time_min // 60:02d}:{current_time_min % 60:02d}"

                # 시간대 구분

                hour = int(start_time_str.split(':')[0])
                if hour < 12: 
                    slot = "morning"
                elif hour < 14:
                    slot = "lunch"
                elif hour < 17:
                    slot = "afternoon"
                elif hour < 19:
                    slot = "dinner"
                else:
                    slot = "night"

                # 같은 타입의 예비 장소 찾기 (최대 5개)
                alternatives = [
                    alt for alt in alternative_places 
                    if alt['type'] == place['type']
                ][:5]
                
                # 각 예비 장소에 이전 장소에서의 거리/시간 정보 추가
                for alt in alternatives:
                    if i > 0:
                        # 이전 장소에서 예비 장소까지의 거리 계산
                        alt_lat1 = prev_place.get('latitude', 0)
                        alt_lon1 = prev_place.get('longitude', 0)
                        alt_lat2 = alt.get('latitude', 0)
                        alt_lon2 = alt.get('longitude', 0)
                        
                        alt_straight_dist = self.optimizer.get_straight_distance(alt_lat1, alt_lon1, alt_lat2, alt_lon2)
                        alt_mode = "walk" if alt_straight_dist < 1.5 else "public"
                        
                        # 예비 장소까지의 이동 정보
                        alt_travel_result = self.optimizer.calculate_distance(
                            alt_lat1, alt_lon1, alt_lat2, alt_lon2,
                            mode=alt_mode
                        )
                        
                        alt['travel_from_previous'] = {
                            "distance_km": alt_travel_result["distance_km"],
                            "time_minutes": alt_travel_result["time_minutes"],
                            "mode": alt_mode,
                            "description": f"이동 {alt_travel_result['time_minutes']}분 ({alt_travel_result['distance_km']}km)",
                            "method": alt_travel_result.get("method", "unknown")
                        }
                    else:
                        # 첫 번째 장소인 경우 이동 정보 없음
                        alt['travel_from_previous'] = None

                schedule_item = {
                    "order": i + 1,
                    "time_slot": slot,
                    "start_time": start_time_str,
                    "end_time": end_time_str,
                    "place": place,
                    "duration_minutes": duration_min,
                    "travel_from_previous": travel_info,
                    "travel_options": travel_options,  # 모든 교통수단 선택지
                    "alternatives": alternatives
                }
                day_plan["schedule"].append(schedule_item)
            day_plan["summary"] = {
                "total_distance_km": round(total_dist, 2),
                "total_travel_time_minutes": total_time
            }
            itinerary.append(day_plan)
        
        # 첫 날에만 클러스터링 정보 저장
        if itinerary and clustering_debug_info:
            itinerary[0]["clustering_debug_info"] = clustering_debug_info
            
        return itinerary