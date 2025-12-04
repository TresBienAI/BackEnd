import json
import os
import time
import asyncio
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text
from db_connection import get_db_session

class SearchService:
    def __init__(self):
        """캐시 초기화 (TTL 포함)"""
        self.destination_cache = {}  # destination별 캐시: {destination: (data, timestamp)}
        self.cache_lock = asyncio.Lock()  # 동시 접근 방지 Lock
        self.cache_ttl = 3600  # TTL: 1시간 (3600초)
        self.cleanup_interval = 600  # 정리 주기: 10분 (600초)
    
    def _is_cache_valid(self, destination: str) -> bool:
        """
        캐시가 유효한지 확인 (TTL 체크)
        """
        if destination not in self.destination_cache:
            return False
        
        places, timestamp = self.destination_cache[destination]
        elapsed = time.time() - timestamp
        
        if elapsed > self.cache_ttl:
            # TTL 만료: 캐시 제거
            del self.destination_cache[destination]
            print(f"⏰ TTL 만료: {destination} 캐시 제거 ({elapsed:.0f}초 경과)")
            return False
        
        return True
    
    def _cleanup_expired_cache(self):
        """
        만료된 캐시 정리 (주기적으로 호출)
        """
        current_time = time.time()
        expired_keys = []
        
        for destination, (places, timestamp) in self.destination_cache.items():
            elapsed = current_time - timestamp
            if elapsed > self.cache_ttl:
                expired_keys.append(destination)
        
        for destination in expired_keys:
            del self.destination_cache[destination]
            print(f"🧹 만료된 캐시 정리: {destination}")
        
        if expired_keys:
            print(f"✅ 총 {len(expired_keys)}개의 만료된 캐시 정리 완료 (캐시 크기: {len(self.destination_cache)}개)")
    
    async def _load_places_by_destination_async(self, destination: str) -> List[dict]:
        """
        특정 destination의 장소 데이터만 로드 (캐싱 + TTL + Lock 적용)
        """
        # 1. 캐시 확인 (TTL 포함)
        if self._is_cache_valid(destination):
            places, _ = self.destination_cache[destination]
            print(f"✅ 캐시에서 {destination} 데이터 로드 ({len(places)}개, 캐시 크기: {len(self.destination_cache)}개)")
            return places
        
        # 2. Lock을 사용하여 동시 DB 쿼리 방지
        async with self.cache_lock:
            # Double-check: Lock 획득 후 다시 캐시 확인
            if self._is_cache_valid(destination):
                places, _ = self.destination_cache[destination]
                print(f"✅ (Lock 후) 캐시에서 {destination} 데이터 로드 ({len(places)}개)")
                return places
            
            # 3. DB에서 데이터 조회
            places = await self._query_from_database(destination)
        
            # 4. DB 쿼리 완료 후 캐시에 저장 (timestamp 포함)
            if places:
                self.destination_cache[destination] = (places, time.time())
                print(f"✅ 데이터베이스에서 {destination} 데이터 로드 완료 ({len(places)}개, 캐시 저장됨)")
            
            # 5. 주기적으로 만료된 캐시 정리
            if len(self.destination_cache) % 10 == 0:  # 10번마다 한 번 정리
                self._cleanup_expired_cache()
            
            return places
    
    async def _query_from_database(self, destination: str) -> List[dict]:
        """
        데이터베이스에서 destination의 장소 데이터 조회
        """
        try:
            session = get_db_session()
            
            # destination 매핑 (사용자 입력을 실제 지역명으로 변환)
            destination_map = {
                '서울': '서울',
                '제주도': '제주',
                '제주': '제주',
                '부산': '부산',
                '인천': '인천',
                '대전': '대전',
                '대구': '대구',
                '광주': '광주'
            }
            search_term = destination_map.get(destination, destination)
            
            # destination에 맞는 데이터만 조회
            query = """
                SELECT 
                    p.id,
                    p.name,
                    p.latitude,
                    p.longitude,
                    p.overview as description,
                    p.address,
                    p.main_type as type,
                    p.sub_type,
                    p.image_url,
                    p.details,
                    p.content_id,
                    p.content_type_id,
                    COALESCE((p.details->>'price_level')::int, 2) as price_level,
                    p.created_at,
                    p.updated_at,
                    ARRAY_AGG(DISTINCT pt.name) FILTER (WHERE pt.name IS NOT NULL) as category
                FROM pois p
                LEFT JOIN poi_tag_association pta ON p.id = pta.poi_id
                LEFT JOIN poi_tags pt ON pta.tag_id = pt.id
                WHERE p.address LIKE :search_term
                GROUP BY p.id, p.name, p.latitude, p.longitude, p.overview, p.address, 
                         p.main_type, p.sub_type, p.image_url, p.content_id, 
                         p.content_type_id, p.created_at, p.updated_at
                ORDER BY p.name
            """
            
            result = session.execute(text(query), {"search_term": f"%{search_term}%"})
            rows = result.fetchall()
            session.close()
            
            # 결과를 딕셔너리로 변환
            places = []
            for row in rows:
                place = {
                    'id': row[0],
                    'name': row[1],
                    'latitude': row[2],
                    'longitude': row[3],
                    'description': row[4],
                    'address': row[5],
                    'type': row[6],
                    'sub_type': row[7],
                    'image_url': row[8],
                    'details': row[9] if row[9] else {},
                    'content_id': row[10],
                    'content_type_id': row[11],
                    'price_level': row[12] or 2,  # NULL이면 기본값 2
                    'created_at': row[13],
                    'updated_at': row[14],
                    'destination': destination,  # 명시적으로 설정
                    'category': list(row[15]) if row[15] else [],  # 태그들
                }
                places.append(place)
            
            return places
            
        except Exception as e:
            print(f"❌ 데이터베이스 조회 중 오류 발생: {str(e)}")
            print("⚠️  JSON 파일로 폴백합니다.")
            # JSON 파일로 폴백
            try:
                file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'sample_data.json')
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
    
    def _load_places_by_destination(self, destination: str) -> List[dict]:
        """
        비동기 함수를 동기 환경에서 호출하기 위한 래퍼 (호환성)
        """
        try:
            # 이미 실행 중인 event loop가 있는 경우
            loop = asyncio.get_running_loop()
            # 새로운 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self._load_places_by_destination_async(destination))
                return future.result()
        except RuntimeError:
            # Event loop가 없는 경우 직접 실행
            return asyncio.run(self._load_places_by_destination_async(destination))
    
    def search_places_with_priority(
        self,
        destination: str,
        travel_styles: List[str],
        requirements: List[str],
        price_level: int) -> List[dict]:
        """
        우선순위 기반 장소 검색 (PostgreSQL 데이터베이스 사용)
        """

        # 1. destination의 데이터 로드 (캐싱 적용)
        all_places = self._load_places_by_destination(destination)
        
        # 2. 예산 필터링
        candidates = [
            p for p in all_places 
            if p.get('price_level', 2) <= price_level
        ]
        # 2. 각 장소 점수 계산
        scored_places = []
        for place in candidates:
            score = self.calculate_place_score(
                place,
                destination,
                travel_styles,
                requirements
            )

            # 점수가 50점 이상인 것만(목적지 일치 필수)
            if score >= 50:
                place['score'] = score
                scored_places.append(place)

        # 3. 점수 내림차순 정렬

        scored_places.sort(key=lambda x: x['score'], reverse=True)

        # 4. 결과 반환
        return scored_places

    def calculate_place_score(
        self,
        place: dict,
        user_destination: str,
        user_travel_styles: List[str],
        user_requirements: List[str]
    ) -> float:
        """
        점수 계산 로직 (이전과 동일)
        """
        score = 0.0

        #1. 여행 목적지(50점)
        if place['destination'] == user_destination:
            score += 50
        else:
            return 0
        
        #2. 여행 스타일(30점)
        place_categories = place.get("category",[])
        matched_styles = 0

        if user_travel_styles:
            for style in user_travel_styles:
                if style in place_categories:
                    matched_styles += 1
                else:
                    # 유사 키워드 매칭
                    similar_keywords = self.get_similar_keywords(style)
                    for keyword in similar_keywords:
                        if keyword in place_categories:
                            matched_styles += 0.5
                            break

            match_ratio = matched_styles / len(user_travel_styles)
            score += match_ratio * 30

        
        # 3. 추가 요구사항 (20점)
        if user_requirements:
            matched_count = 0
            for req in user_requirements:
                if req in place_categories:
                    matched_count +=1

            match_ratio = matched_count / len(user_requirements)
            score += match_ratio * 20

        return score

    def get_similar_keywords(self, travel_style: str) -> List[str]:
        """
        유사 키워드 매핑 (이전과 동일)
        """
        similar_map = {
            "힐링": ["자연", "조용한", "휴식", "스파", "산책"],
            "맛집 투어": ["전통음식", "로컬맛집", "음식", "해산물"],
            "역사위주": ["문화체험", "전통", "유적지", "박물관"],
            "카페 투어": ["카페", "디저트", "커피"],
            "팝업 스토어": ["전시", "쇼핑", "트렌디", "갤러리"],
            "로맨틱한 장소": ["커플", "데이트", "야경", "로맨틱"],
            "액티비티": ["체험", "등산", "해변", "수영"]
        }
        return similar_map.get(travel_style, [])