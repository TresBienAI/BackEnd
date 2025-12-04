import math
import requests
import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

class RouteOptimizer:
    def __init__(self):
        # Azure Maps 설정
        self.use_azure_maps = os.getenv("USE_AZURE_MAPS", "false").lower() == "true"
        self.azure_maps_key = os.getenv("AZURE_MAPS_SUBSCRIPTION_KEY")

        self.cache = {}
        self.cache_max_size = 5000  # 캐시 크기 확대: 1000 → 5000

    def get_straight_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """직선 거리 계산 (km)"""
        return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    async def calculate_distance_async(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        mode: str = "public"
    ) -> Dict[str, float]:
        """
        비동기 거리 계산 (I/O 작업)
        
        Azure Maps API 호출이나 캐시 조회 시 대기 시간이 발생하므로
        비동기로 처리하여 다른 작업과 병렬 실행 가능
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.calculate_distance,
            lat1, lon1, lat2, lon2, mode
        )

    def calculate_distance(
        self,
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float,
        mode: str = "public"
    ) -> Dict[str,float]:
        """
        거리 및 시간 계산 (하이브리드)
        
        Args:
            lat1, lon1: 출발지 좌표
            lat2, lon2: 도착지 좌표
            mode: 교통수단 ("walk", "car", "public")
        
        Returns:
            {
                "distance_km": 5.8,
                "time_minutes": 18,
                "method": "azure_maps" or "haversine"
            }
        """
        # Null 체크
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return {"distance_km": 0.0, "time_minutes": 0, "method": "none"}

        # 1. 캐시 확인
        cache_key = f"{lat1:.4f}, {lon1:.4f}, {lat2:.4f}, {lon2:.4f}:{mode}"
        if cache_key in self.cache:
            result = self.cache[cache_key].copy()
            result["method"] = "cache"
            return result
        
        # 2. 직선 거리 계산
        straight_dist = self._haversine_distance(lat1, lon1, lat2, lon2)

        # 3. 조건별 선택
        if not self.use_azure_maps:
            # Azure Maps 비활성화 -> Haversine 사용
            result = self._calculate_with_haversine(lat1, lon1, lat2, lon2, mode)
        elif straight_dist < 1.5:
            # 1.5km 미만 -> Haversine 사용
            result = self._calculate_with_haversine(lat1, lon1, lat2, lon2, mode)
        elif mode == "walk":
            # Walk는 항상 Haversine 사용 (실제 도로와 무관하게 직선 거리 기반)
            result = self._calculate_with_haversine(lat1, lon1, lat2, lon2, mode)
        else:
            # 1.5km 이상 + public/car -> Azure Maps 사용 (1차 선택)
            result = self._calculate_with_azure_maps(lat1, lon1, lat2, lon2, mode)
            if result.get("method") == "error":
                # Azure Maps 실패 시 Haversine으로 폴백
                result = self._calculate_with_haversine(lat1, lon1, lat2, lon2, mode)
        
        self._add_to_cache(cache_key, result)
        return result

    def _haversine_distance(
        self,
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """Haversine 공식을 사용한 거리 계산"""

        R = 6371.0  # 지구 반지름 (km)

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
            math.cos(math.radians(lat1))*math.cos(math.radians(lat2)) * 
            math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c
        
        return round(d,2)
    
    async def haversine_distance_async(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        비동기 Haversine 거리 계산 (CPU-bound 작업)
        
        여러 거리를 동시에 계산할 때 활용
        각 계산이 독립적이고 CPU 작업이므로 thread pool에서 실행 가능
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._haversine_distance,
            lat1, lon1, lat2, lon2
        )

    def _calculate_with_haversine(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        mode: str
    ) -> Dict[str,float]:
        """
        Haversine 공식을 사용한 거리 및 시간 계산
        """
        distance_km = round(self._haversine_distance(lat1, lon1, lat2, lon2), 2)
        
        # 교통수단별 속도
        speed_map = {
            "walk": 4.0,
            "car": 30.0,
            "public": 20.0
        }

        speed = speed_map.get(mode, 20.0)

        # 시간 계산
        time_minutes = round(distance_km / speed * 60) + 10

        return {
            "distance_km": distance_km,
            "time_minutes": time_minutes,
            "method": "haversine"
        }


    def _calculate_with_azure_maps(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        mode: str = "public"
    ) -> Dict[str,float]:
        """
        Azure Maps를 사용한 거리 및 시간 계산
        """
        # 교통수단 매핑
        travel_mode_map = {
            "car" : "car",
            "public" : "publicTransit",
            "walk" : "pedestrian"
        }

        travel_mode = travel_mode_map.get(mode, "car")

        #Azure Maps Route API
        url = "https://atlas.microsoft.com/route/directions/json"
        params = {
            "api-version": "1.0",
            "subscription-key": self.azure_maps_key,
            "query": f"{lat1},{lon1}:{lat2},{lon2}",
            "travelMode": travel_mode,
            "traffic": "true",
            "departAt": datetime.now().isoformat()
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("routes"):
                route = data["routes"][0]
                summary = route["summary"]

                # 거리 (미터 -> km)
                distance_km = round(summary['lengthInMeters'] / 1000, 2)

                # 소요 시간 (초 -> 분)
                time_minutes = round(summary['travelTimeInSeconds'] / 60)

                return {
                    "distance_km": distance_km,
                    "time_minutes": time_minutes,
                    "method": "azure_maps"
                }
            else:
                # routes가 없는 경우
                return {"method": "error"}
        except Exception as e:
            print(f"Azure Maps API Error: {e}")
            return {"method": "error"}

    def cluster_places(self, places: List[Dict], k: int) -> List[List[Dict]]:
        """
        K-Means 알고리즘을 사용하여 장소들을 k개의 그룹(일자별)으로 나눔
        (외부 라이브러리 없이 구현)
        """
        if not places or k <= 0:
            return []
        
        if len(places) <= k:
            return [[p] for p in places]

        # 1. 초기 중심점 설정 (첫 k개 장소를 중심으로 사용 - 간단 버전)
        centroids = [
            (p['latitude'], p['longitude']) 
            for p in places[:k]
        ]
        
        # 최대 10번 반복 (보통 금방 수렴함)
        for _ in range(10):
            # 클러스터 초기화
            new_clusters = [[] for _ in range(k)]
            
            # 2. 각 장소를 가장 가까운 중심점에 할당
            for place in places:
                p_lat, p_lon = place['latitude'], place['longitude']
                
                best_cluster_idx = 0
                min_dist = float('inf')
                
                for i, (c_lat, c_lon) in enumerate(centroids):
                    # 직선 거리 계산 (빠름)
                    dist = self._haversine_distance(p_lat, p_lon, c_lat, c_lon)
                    if dist < min_dist:
                        min_dist = dist
                        best_cluster_idx = i
                
                new_clusters[best_cluster_idx].append(place)
            
            # 3. 중심점 업데이트
            new_centroids = []
            
            for cluster in new_clusters:
                if not cluster: # 빈 클러스터면 기존 중심 유지
                    new_centroids.append(centroids[len(new_centroids)])
                    continue
                    
                avg_lat = sum(p['latitude'] for p in cluster) / len(cluster)
                avg_lon = sum(p['longitude'] for p in cluster) / len(cluster)
                new_centroids.append((avg_lat, avg_lon))
            
            centroids = new_centroids
            clusters = new_clusters

        return clusters

    def _add_to_cache(self, key: str, value: Dict):
        """캐시에 추가 (최대 크기 제한)"""
        if len(self.cache) >= self.cache_max_size:
            # 가장 오래된 항목 삭제 (FIFO)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[key] = value

    def calculate_travel_time(self, distance_km: float, mode:str = "public") -> int:
        """
        거리와 이동 수단에 따른 예상 소요 시간(분) 계산
        """
        if mode == "walk":
            speed_kmh = 4.0
        elif mode == 'car':
            speed_kmh = 30.0 # 도심 주행 평균 속도
        else: #public (대중교통)
            speed_kmh = 20.0 # 대기 시간 포함 평균 속도
        
        time_hours = distance_km / speed_kmh
        return int(time_hours * 60) + 10 # 10분 여유 시간 추가
    
    def optimize_route(self, places: List[Dict], start_location: Optional[Dict] = None) -> List[Dict]:
        """
        Greedy Nearest Neighbor 알고리즘으로 최단 경로 정렬
        """
        if not places:
            return []
        
        unvisited = places.copy()
        route = []

        # 시작점 결정
        if start_location:
            current_location = start_location
            route.append(current_location)
        else:
            # 시작점이 없으면 점수가 가장 높은 곳을 첫 번째로 선택
            current_location = max(unvisited, key=lambda x: x.get('score', 0))
            unvisited.remove(current_location)
            route.append(current_location)

        # 가장 가까운 곳을 찾아가며 경로 생성
        while unvisited:
            nearest_place = None
            min_dist = float("inf")

            for place in unvisited:
                result = self.calculate_distance(
                    current_location.get('latitude',0),
                    current_location.get('longitude',0),
                    place.get('latitude',0),
                    place.get('longitude',0)
                )
                dist = result["distance_km"]
                if dist < min_dist:
                    min_dist = dist
                    nearest_place = place
            if nearest_place:
                route.append(nearest_place)
                unvisited.remove(nearest_place)
                current_location = nearest_place
            else:
                break
        return route