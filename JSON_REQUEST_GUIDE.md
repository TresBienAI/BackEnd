# 📋 `/travel/plans` JSON 요청/응답 가이드

## 🎯 빠른 시작

### 최소 요청 (필수 필드만)

```json
{
  "destination": "제주도",
  "start_date": "2025-12-20",
  "travel_styles": ["자연"],
  "duration_days": 3,
  "budget": "100만원"
}
```

### 전체 요청 (모든 필드)

```json
{
  "destination": "제주도",
  "start_date": "2025-12-20",
  "travel_styles": ["자연", "맛집"],
  "duration_days": 3,
  "budget": "150만원",
  "requirements": ["가족여행", "사진촬영"],
  "budget_level": 2,
  "include_debug": true
}
```

---

## 📨 cURL 예시

### 기본 요청

```bash
curl -X POST "http://localhost:8000/travel/plans" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "제주도",
    "start_date": "2025-12-20",
    "travel_styles": ["자연", "맛집"],
    "duration_days": 3,
    "budget": "150만원"
  }'
```

### 상세 정보 포함 요청

```bash
curl -X POST "http://localhost:8000/travel/plans" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "제주도",
    "start_date": "2025-12-20",
    "travel_styles": ["자연", "맛집"],
    "duration_days": 3,
    "budget": "150만원",
    "requirements": ["가족여행"],
    "include_debug": true
  }'
```

---

## 📥 요청 필드 상세

### 필수 필드

| 필드 | 타입 | 예시 | 설명 |
|------|------|------|------|
| **destination** | string | "제주도" | 여행지 |
| **start_date** | string | "2025-12-20" | 출발 날짜 |
| **travel_styles** | array | ["자연", "맛집"] | 여행 스타일 (배열) |
| **duration_days** | integer | 3 | 여행 기간 (일수) |
| **budget** | string | "150만원" | 예산 |

### 선택 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| **requirements** | array | [] | 추가 요구사항 |
| **budget_level** | integer | null (자동계산) | 예산 등급 (1~3) |
| **include_debug** | boolean | true | 점수/클러스터링 포함 |

---

## 📤 응답 구조

### 최상위 응답

```json
{
  "success": true,
  "message": "여행 일정이 성공적으로 생성되었습니다.",
  "data": {
    "destination": "제주도",
    "duration_days": 3,
    "total_places": 8,
    "itinerary": [...],
    "debug_info": {...}
  }
}
```

### 데이터 구조 상세

```json
{
  "success": true,
  "message": "여행 일정이 성공적으로 생성되었습니다.",
  "data": {
    // 1️⃣ 기본 정보
    "destination": "제주도",
    "duration_days": 3,
    "total_places": 8,
    
    // 2️⃣ 일정 배열
    "itinerary": [
      {
        "day": 1,
        "schedule": [
          {
            "order": 1,
            "time_slot": "morning",
            "start_time": "09:00",
            "end_time": "10:30",
            "place": {
              "name": "제주 힐링 리조트",
              "type": "hotel",
              "destination": "제주도",
              "latitude": 33.2541,
              "longitude": 126.4123,
              "rating": 4.7,
              "price_range": 3,
              "score": 50.0
            },
            "duration_minutes": 90,
            "travel_from_previous": null,  // 첫 번째 장소
            "travel_options": null,
            "alternatives": []
          },
          {
            "order": 2,
            "time_slot": "night",
            "start_time": "23:34",
            "end_time": "25:04",
            "place": {
              "name": "셕지코지",
              "type": "activity",
              "destination": "제주도",
              "latitude": 33.4242,
              "longitude": 126.9288,
              "rating": 4.8,
              "price_range": 1,
              "score": 65.0
            },
            "duration_minutes": 90,
            "travel_from_previous": {
              "distance_km": 51.57,
              "time_minutes": 784,
              "mode": "walk",
              "description": "walk - 784분 (51.57km)",
              "method": "cache"
            },
            "travel_options": {
              "walk": {
                "distance_km": 51.57,
                "time_minutes": 784,
                "mode": "walk",
                "method": "cache"
              },
              "public": {
                "distance_km": 51.57,
                "time_minutes": 165,
                "mode": "public",
                "method": "cache"
              }
            },
            "alternatives": []
          }
        ],
        "summary": {
          "total_distance_km": 109.8,
          "total_travel_time_minutes": 1677
        }
      }
    ],
    
    // 3️⃣ 디버그 정보 (include_debug=true일 때만)
    "debug_info": {
      "total_searched_places": 8,
      "selected_places_count": 8,
      "alternative_places_count": 0,
      "selected_places": [
        {
          "name": "셕지코지",
          "type": "activity",
          "score": 65.0,
          "latitude": 33.4242,
          "longitude": 126.9288,
          "rating": 4.8,
          "price_range": 1
        }
      ],
      "clustering": {
        "clustering_method": "K-Means",
        "total_places_for_clustering": 7,
        "num_clusters": 3,
        "clusters": [
          {
            "day": 1,
            "places_in_cluster": 2,
            "cluster_places": [
              {
                "name": "셕지코지",
                "type": "activity",
                "score": 65.0,
                "latitude": 33.4242,
                "longitude": 126.9288
              }
            ]
          }
        ]
      }
    }
  }
}
```

---

## 🔍 각 필드 설명

### `place` 객체

```json
{
  "name": "성산일출봉",
  "type": "attraction",           // hotel, activity, restaurant, cafe
  "destination": "제주도",
  "sub_region": "성산읍",
  "description": "제주도 대표 일출 명소",
  "latitude": 33.4584,
  "longitude": 126.9424,
  "rating": 4.6,                  // 평점
  "price_range": 1,               // 1: 저가, 2: 중간, 3: 고가
  "review_count": 3421,
  "recommended_duration": "2-3시간",
  "address": "제주특별자치도 서귀포시...",
  "image_url": "https://...",
  "category": ["자연", "등산", "사진"],
  "score": 65.0                   // ⭐ 스타일 매칭 점수
}
```

### `travel_options` 객체

```json
{
  "walk": {
    "distance_km": 4.5,
    "time_minutes": 25,
    "mode": "walk",
    "description": "walk - 25분 (4.5km)",
    "method": "haversine"          // haversine, azure_maps, cache
  },
  "public": {
    "distance_km": 4.5,
    "time_minutes": 12,
    "mode": "public",
    "description": "public - 12분 (4.5km)",
    "method": "cache"
  }
}
```

**method 종류:**
- `haversine`: 직선 거리 계산 (1.5km 미만)
- `azure_maps`: Azure Maps API (1.5km 이상, 정확함)
- `cache`: 이전 계산 결과 재사용 (빠름)

---

## 📊 여행 스타일 목록

```javascript
const availableStyles = [
  "힐링",
  "자연",
  "맛집",
  "음식",
  "관광",
  "액티비티",
  "역사",
  "문화체험",
  "쇼핑",
  "카페",
  "로맨틱",
  "가족여행",
  // ... 더 많음
];

// 요청 예시
{
  "travel_styles": ["자연", "맛집"]  // 배열로 여러 개 가능
}
```

---

## 💰 예산 포맷

```javascript
// 지원하는 예산 포맷들
{
  "budget": "50만원"        // ✅ 권장
}

{
  "budget": "500000"        // ✅ 숫자만
}

{
  "budget": "100만원"       // ✅
}

{
  "budget": "1억원"         // ✅
}

{
  "budget": "3,000,000"     // ✅ 콤마 포함
}
```

**자동 계산:**
- 50만원 ÷ 3일 = 16.7만원/일 → budget_level = 2 (중간)
- 10만원 ÷ 3일 = 3.3만원/일 → budget_level = 1 (저가)
- 150만원 ÷ 3일 = 50만원/일 → budget_level = 3 (고가)

---

## 🗓️ start_date 포맷

```javascript
// 모두 지원됨 (AI가 자동으로 정규화)
{
  "start_date": "2025-12-20"      // ✅ ISO 8601 (권장)
}

{
  "start_date": "12월 20일"       // ✅ 한국식
}

{
  "start_date": "2025년 12월 20일" // ✅ 상세 한국식
}

{
  "start_date": "Dec 20"          // ✅ 영어식
}

{
  "start_date": "20/12/2025"      // ✅ 유럽식
}
```

---

## 🎯 budget_level 가이드

```javascript
// 자동 계산 (권장)
{
  "destination": "제주도",
  "duration_days": 3,
  "budget": "100만원"
  // budget_level 자동 계산됨
}

// 수동 지정
{
  "destination": "제주도",
  "duration_days": 3,
  "budget": "100만원",
  "budget_level": 2              // 1: 저가, 2: 중간, 3: 고가
}
```

### 기준 (1인 1일)

| Level | 예산 | 특징 |
|-------|------|------|
| **1** | ≤ 10만원 | 저가 맛집, 무료 관광지 |
| **2** | 10~30만원 | 중간 음식점, 일반 관광지 |
| **3** | ≥ 30만원 | 고급 음식점, 프리미엄 활동 |

---

## 🧪 JavaScript 예시

### Fetch API

```javascript
const response = await fetch('http://localhost:8000/travel/plans', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    destination: '제주도',
    start_date: '2025-12-20',
    travel_styles: ['자연', '맛집'],
    duration_days: 3,
    budget: '150만원',
    requirements: ['가족여행'],
    include_debug: true
  })
});

const data = await response.json();

// 응답 사용
console.log(`${data.data.destination} ${data.data.duration_days}일 일정`);
console.log(`총 ${data.data.total_places}개 장소`);

// 일정 순회
data.data.itinerary.forEach(day => {
  console.log(`Day ${day.day}:`);
  day.schedule.forEach(item => {
    console.log(`  ${item.start_time} - ${item.place.name}`);
  });
});

// 점수 확인
if (data.data.debug_info) {
  data.data.debug_info.selected_places.forEach(place => {
    console.log(`${place.name}: ${place.score}점`);
  });
}
```

### Axios

```javascript
const axios = require('axios');

const response = await axios.post('http://localhost:8000/travel/plans', {
  destination: '제주도',
  start_date: '2025-12-20',
  travel_styles: ['자연', '맛집'],
  duration_days: 3,
  budget: '150만원'
});

console.log(response.data.data.itinerary);
```

### React Hook

```javascript
import { useState } from 'react';

function TravelPlanner() {
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);

  const generatePlan = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/travel/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: '제주도',
          start_date: '2025-12-20',
          travel_styles: ['자연', '맛집'],
          duration_days: 3,
          budget: '150만원'
        })
      });
      
      const data = await response.json();
      setItinerary(data.data.itinerary);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>계획 생성 중...</div>;
  
  return (
    <div>
      <button onClick={generatePlan}>여행 계획 생성</button>
      
      {itinerary && itinerary.map((day) => (
        <div key={day.day}>
          <h2>Day {day.day}</h2>
          {day.schedule.map((item, idx) => (
            <div key={idx}>
              <h3>{item.place.name}</h3>
              <p>{item.start_time} - {item.end_time}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

---

## ⚠️ 에러 처리

```javascript
try {
  const response = await fetch('http://localhost:8000/travel/plans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({...})
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.detail);
    return;
  }

  const data = await response.json();
  console.log('Success:', data);
} catch (error) {
  console.error('Request failed:', error);
}
```

---

## 🔗 관련 엔드포인트

### 같은 정보로 `/chat/travel` 사용

```bash
# 첫 메시지
curl -X POST "http://localhost:8000/chat/travel" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "제주도 여행 가고 싶어",
    "thread_id": "user-123"
  }'

# AI가 자동으로 start_date, duration 등 물어봄
# 대화로 정보 수집 후 같은 일정 생성
```

---

## ✅ 체크리스트

- [ ] destination 지정
- [ ] start_date 지정 (YYYY-MM-DD 권장)
- [ ] travel_styles 최소 1개 이상
- [ ] duration_days 지정
- [ ] budget 지정
- [ ] JSON 형식 확인
- [ ] Content-Type: application/json 헤더 확인

🎉 완료!

