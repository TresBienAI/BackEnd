# 프론트엔드 개발 가이드

프론트엔드에서 Travel Planner API를 사용하기 위한 완벽한 가이드입니다.

## 📋 목차

1. [🔐 로그인 & 인증](#🔐-로그인--인증)
2. [시작하기](#시작하기)
3. [API 엔드포인트](#api-엔드포인트)
4. [데이터 구조](#데이터-구조)
5. [요청/응답 예시](#요청응답-예시)
6. [주요 기능 구현](#주요-기능-구현)
7. [에러 처리](#에러-처리)
8. [React 예제](#react-예제)
9. [Vue.js 예제](#vuejs-예제)

---

## 🔐 로그인 & 인증

### 📝 인증 흐름

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: 카카오 로그인                                    │
│ https://gallemalle-auth-service.../login               │
│ → access_token 받음                                     │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: 토큰 검증 (인증 서버)                           │
│ POST https://gallemalle-auth-service.../travel         │
│ Header: Authorization: Bearer {access_token}          │
│ → X-User-ID 헤더 추가됨                                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: 우리 서버에 요청                               │
│ POST http://localhost:8000/travel/plans               │
│ Header: X-User-ID: {user_id}                          │
│ → 플랜 생성 & DB에 저장                               │
└─────────────────────────────────────────────────────────┘
```

### 1️⃣ 카카오 로그인

```html
<!-- 카카오 로그인 버튼 -->
<a href="https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/login">
  카카오로 로그인
</a>
```

### 2️⃣ 토큰 저장 및 사용

```javascript
// 1. 로그인 후 URL에서 access_token 추출
const urlParams = new URLSearchParams(window.location.search);
const accessToken = urlParams.get('access_token');

// 2. localStorage에 저장
if (accessToken) {
  localStorage.setItem('accessToken', accessToken);
  // 카카오 로그인 서버로 리다이렉트
  window.location.href = 'https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/travel';
}

// 3. 저장된 토큰으로 X-User-ID 얻기 (인증 서버가 헤더 추가)
const token = localStorage.getItem('accessToken');
```

### 3️⃣ 인증이 필요한 API 요청

```javascript
// ⭐ 중요: X-User-ID 헤더 필수!
async function apiRequest(endpoint, method = "GET", data = null, userId = null) {
  const headers = {
    "Content-Type": "application/json",
  };

  // X-User-ID 헤더 추가 (인증이 필요한 엔드포인트)
  if (userId) {
    headers["X-User-ID"] = userId;
  }

  const options = {
    method,
    headers,
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`http://localhost:8000${endpoint}`, options);

    if (response.status === 401) {
      // 인증 실패 - 다시 로그인
      alert("인증이 필요합니다. 다시 로그인해주세요.");
      window.location.href = 'https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/login';
      return;
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API 요청 실패:", error.message);
    throw error;
  }
}
```

### 4️⃣ 로그인 상태 확인

```javascript
function isLoggedIn() {
  return !!localStorage.getItem('accessToken');
}

function logout() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('userId');
  window.location.href = '/';
}

// 페이지 로드 시 확인
if (!isLoggedIn()) {
  window.location.href = 'https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/login';
}
```

### 5️⃣ 사용자 ID 저장하기 (인증 서버 콜백)

```javascript
// 인증 서버가 우리 서버로 X-User-ID 헤더 추가해서 요청할 때
// 우리는 첫 번째 API 요청에서 user_id를 얻을 수 있습니다

async function getUserIdFromServer(accessToken) {
  try {
    // 인증 서버가 X-User-ID를 헤더에 추가해서 전달
    const response = await fetch('https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/travel', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    // 응답 헤더에서 X-User-ID 추출
    const userId = response.headers.get('X-User-ID');
    if (userId) {
      localStorage.setItem('userId', userId);
      return userId;
    }
  } catch (error) {
    console.error("User ID 조회 실패:", error);
  }
}
```

---

## 시작하기

### API 서버 연결

```javascript
const API_BASE_URL = "http://localhost:8000";

// ⭐ 개선된 요청 함수 (X-User-ID 헤더 포함)
async function apiRequest(endpoint, method = "GET", data = null, userId = null) {
  const headers = {
    "Content-Type": "application/json",
  };

  // X-User-ID 헤더 추가 (인증이 필요한 엔드포인트)
  if (userId) {
    headers["X-User-ID"] = userId;
  }

  const options = {
    method,
    headers,
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (response.status === 401) {
      // 인증 실패
      console.error("인증 실패: X-User-ID 헤더가 필요합니다.");
      throw new Error("인증이 필요합니다. 다시 로그인해주세요.");
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API 요청 실패:", error.message);
    throw error;
  }
}

// 사용 예시: userId와 함께 호출
// const plan = await apiRequest("/travel/plans", "POST", planData, userId);
```

---

## API 엔드포인트

### 1. GET /travel/destinations
지원하는 여행지 목록을 조회합니다.

**요청:**
```javascript
const destinations = await apiRequest("/travel/destinations");
```

**응답:**
```json
{
  "destinations": ["서울", "제주도", "부산"]
}
```

**사용 예:**
```javascript
const { destinations } = await apiRequest("/travel/destinations");
console.log(destinations); // ["서울", "제주도", "부산"]
```

---

### 2. GET /travel/types
지원하는 여행 타입을 조회합니다.

**요청:**
```javascript
const types = await apiRequest("/travel/types");
```

**응답:**
```json
{
  "types": ["힐링", "음식", "관광", "액티비티"]
}
```

---

### 3. POST /travel/plans (⭐ 인증 필수)
여행 일정을 생성하고 DB에 저장합니다.

**⭐ 필수 헤더:**
```
X-User-ID: {user_id}
```

**요청:**
```javascript
const userId = localStorage.getItem('userId'); // 로그인한 사용자 ID

const planRequest = {
  destination: "서울",
  start_date: "2025-12-20",
  travel_styles: ["자연", "맛집"],
  duration_days: 2,
  budget: "100만원",
  requirements: [],
  include_debug: false
};

// ⭐ userId를 함께 전달
const plan = await apiRequest("/travel/plans", "POST", planRequest, userId);
```

**응답 구조:**
```json
{
  "success": true,
  "plan_id": "b1fe4398-3116-4ba8-99bd-4133c601cdb6",
  "user_id": "5",
  "destination": "서울",
  "duration_days": 2,
  "message": "여행 일정이 성공적으로 생성되고 저장되었습니다.",
  "data": {
    "destination": "서울",
    "duration_days": 2,
    "total_places": 10,
    "itinerary": [
      {
        "day": 1,
        "schedule": [
          {
            "name": "그린랩",
            "type": "음식점",
            "latitude": 37.5607,
            "longitude": 126.9735
          }
        ]
      }
    ],
    "debug_info": {
      "total_searched_places": 6653,
      "selected_places_count": 10,
      "alternative_places_count": 20,
      "selected_places": [...],
      "alternative_places": [...]
    }
  }
}
```

**💾 저장되는 위치:**
- 데이터베이스: PostgreSQL
- 테이블: `user_travel_plans`
- 저장 정보:
  - `plan_id`: 생성된 플랜의 고유 ID (UUID)
  - `user_id`: 로그인한 사용자 ID
  - `destination`: 여행지
  - `duration_days`: 여행 기간
  - `plan_data`: 전체 1일차, 2일차 일정 + 예비 후보 (JSON)

---

### 4. GET /travel/plans (⭐ 인증 필수)
사용자의 모든 저장된 플랜 조회

**⭐ 필수 헤더:**
```
X-User-ID: {user_id}
```

**요청:**
```javascript
const userId = localStorage.getItem('userId');

// 사용자의 모든 플랜 조회
const response = await apiRequest("/travel/plans", "GET", null, userId);
```

**응답:**
```json
{
  "success": true,
  "user_id": "5",
  "plans": [
    {
      "plan_id": "b1fe4398-3116-4ba8-99bd-4133c601cdb6",
      "destination": "서울",
      "duration_days": 2,
      "created_at": "2025-12-04T11:37:54.470733",
      "updated_at": "2025-12-04T11:37:54.470741"
    }
  ],
  "total_count": 2,
  "limit": 10,
  "offset": 0
}
```

---

### 5. GET /travel/plans/{plan_id} (⭐ 인증 필수)
저장된 특정 플랜 조회

**요청:**
```javascript
const userId = localStorage.getItem('userId');
const planId = "b1fe4398-3116-4ba8-99bd-4133c601cdb6";

const plan = await apiRequest(`/travel/plans/${planId}`, "GET", null, userId);
```

**응답:**
```json
{
  "success": true,
  "plan_id": "b1fe4398-3116-4ba8-99bd-4133c601cdb6",
  "user_id": "5",
  "destination": "서울",
  "duration_days": 2,
  "plan_data": {
    "itinerary": [
      {
        "day": 1,
        "schedule": [...]
      }
    ]
  }
}
```

---

### 6. POST /travel/plans/update-hotel (⭐ 인증 필수)
호텔을 변경하고 일정을 재계산합니다.

**요청:**
```javascript
const userId = localStorage.getItem('userId');

const hotelChangeRequest = {
  destination: "서울",
  travel_styles: ["자연"],
  duration_days: 2,
  budget: "100만원",
  selected_places: [...], // 기존 선택 장소들 (호텔 제외)
  new_hotel: {
    name: "새로운 호텔",
    latitude: 37.55,
    longitude: 127.00,
    type: "숙박"
  },
  requirements: []
};

// ⭐ userId를 함께 전달
const newPlan = await apiRequest(
  "/travel/plans/update-hotel",
  "POST",
  hotelChangeRequest,
  userId
);
```

---

### 7. POST /travel/plans/replace-place (⭐ 인증 필수)
특정 장소를 다른 장소로 교체합니다.

**요청:**
```javascript
const userId = localStorage.getItem('userId');

const replaceRequest = {
  day: 1,
  old_place: {
    name: "기존 장소",
    latitude: 37.1234,
    longitude: 126.5678,
    type: "관광지"
  },
  new_place: {
    name: "새로운 장소",
    latitude: 37.5760,
    longitude: 126.9767,
    type: "관광지"
  },
  all_places: [...], // 현재 모든 장소
  destination: "서울",
  travel_styles: ["자연"],
  duration_days: 2,
  budget: "100만원",
  requirements: []
};

// ⭐ userId를 함께 전달
const updatedPlan = await apiRequest(
  "/travel/plans/replace-place",
  "POST",
  replaceRequest,
  userId
);
```

---

### 8. DELETE /travel/plans/{plan_id} (⭐ 인증 필수)
저장된 플랜 삭제

**요청:**
```javascript
const userId = localStorage.getItem('userId');
const planId = "b1fe4398-3116-4ba8-99bd-4133c601cdb6";

const response = await apiRequest(`/travel/plans/${planId}`, "DELETE", null, userId);
```

**응답:**
```json
{
  "success": true,
  "message": "플랜이 성공적으로 삭제되었습니다.",
  "plan_id": "b1fe4398-3116-4ba8-99bd-4133c601cdb6"
}
```

---

## 데이터 구조

### Place 객체

```typescript
interface Place {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  type: string; // "숙박", "음식점", "관광지", "문화시설", "레저스포츠", "쇼핑"
  description: string;
  address: string;
  image_url: string;
  category: string[];
  price_level: number; // 1-4
  score: number; // 0-100
}
```

### Schedule Item 객체

```typescript
interface ScheduleItem {
  order: number;
  time_slot: string;
  start_time: string; // "09:00"
  end_time: string; // "10:30"
  place: Place;
  duration_minutes: number;
  travel_from_previous: TravelInfo;
  travel_options: {
    walk: TravelInfo;
    public?: TravelInfo;
    car?: TravelInfo;
  };
  alternatives: PlaceAlternative[];
}

interface TravelInfo {
  distance_km: number;
  time_minutes: number;
  mode: string; // "walk", "public", "car"
  method: string; // "haversine", "azure_maps"
}

interface PlaceAlternative {
  name: string;
  type: string;
  score: number;
  travel_from_previous: TravelInfo;
}
```

### Day 객체

```typescript
interface Day {
  day: number;
  schedule: ScheduleItem[];
  summary: {
    total_distance_km: number;
    total_travel_time_minutes: number;
  };
}
```

---

## 요청/응답 예시

### 예시 1: 서울 2박 3일 여행 계획

**요청:**
```javascript
const response = await apiRequest("/travel/plans", "POST", {
  destination: "서울",
  start_date: "2025-12-20",
  travel_styles: ["자연", "맛집"],
  duration_days: 3,
  budget: "150만원",
  requirements: ["가족여행"],
  include_debug: false
});
```

**응답 (축약):**
```json
{
  "success": true,
  "message": "여행 일정이 성공적으로 생성되었습니다.",
  "data": {
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
            "end_time": "10:30",
            "place": {
              "name": "강남역",
              "latitude": 37.4979,
              "longitude": 127.0276,
              "type": "숙박",
              "score": 85
            },
            "duration_minutes": 90,
            "travel_from_previous": null,
            "travel_options": {}
          },
          {
            "order": 2,
            "time_slot": "late_morning",
            "start_time": "11:00",
            "end_time": "12:30",
            "place": {
              "name": "명동",
              "latitude": 37.5605,
              "longitude": 126.9807,
              "type": "쇼핑",
              "score": 88
            },
            "duration_minutes": 90,
            "travel_from_previous": {
              "distance_km": 2.1,
              "time_minutes": 15,
              "mode": "public",
              "method": "azure_maps"
            },
            "travel_options": {
              "walk": {
                "distance_km": 2.1,
                "time_minutes": 25,
                "mode": "walk",
                "method": "haversine"
              },
              "public": {
                "distance_km": 2.1,
                "time_minutes": 15,
                "mode": "public",
                "method": "azure_maps"
              }
            }
          }
        ],
        "summary": {
          "total_distance_km": 12.5,
          "total_travel_time_minutes": 60
        }
      }
    ]
  }
}
```

---

## 주요 기능 구현

### 1️⃣ 여행 계획 생성 (⭐ 인증 필수)

```javascript
async function generateTravelPlan(formData) {
  try {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      throw new Error("로그인이 필요합니다.");
    }

    // ⭐ userId를 함께 전달
    const response = await apiRequest("/travel/plans", "POST", {
      destination: formData.destination,
      start_date: formData.startDate,
      travel_styles: formData.travelStyles,
      duration_days: formData.durationDays,
      budget: formData.budget,
      requirements: formData.requirements,
      include_debug: false
    }, userId);  // ← userId 추가

    // 응답에는 plan_id가 포함됨
    console.log("생성된 플랜 ID:", response.plan_id);
    
    // localStorage에 현재 플랜 ID 저장 (필요시)
    localStorage.setItem('currentPlanId', response.plan_id);

    return response.data;
  } catch (error) {
    console.error("계획 생성 실패:", error);
    throw error;
  }
}
```

### 2️⃣ 교통수단 선택

사용자가 이동 수단을 선택하면 시간을 자동으로 업데이트합니다.

```javascript
function updateTransportMode(itinerary, dayIndex, itemIndex, mode) {
  const day = itinerary[dayIndex];
  const item = day.schedule[itemIndex];
  
  // 선택된 이동 수단 정보
  const selectedTravel = item.travel_options[mode];
  if (!selectedTravel) return itinerary;

  // 시간 차이 계산
  const oldTime = item.travel_from_previous.time_minutes;
  const newTime = selectedTravel.time_minutes;
  const timeDiff = oldTime - newTime;

  // 현재 item의 start_time 업데이트
  const previousItem = itemIndex > 0 ? day.schedule[itemIndex - 1] : null;
  if (previousItem) {
    const newStartTime = subtractMinutes(previousItem.end_time, newTime);
    item.start_time = newStartTime;
    item.end_time = addMinutes(newStartTime, item.duration_minutes);
  }

  // 다음 item들 시간 업데이트
  for (let i = itemIndex + 1; i < day.schedule.length; i++) {
    const nextItem = day.schedule[i];
    nextItem.start_time = addMinutes(day.schedule[i - 1].end_time, 
      day.schedule[i].travel_from_previous?.time_minutes || 0);
    nextItem.end_time = addMinutes(nextItem.start_time, nextItem.duration_minutes);
  }

  // 선택된 이동 수단 저장
  item.travel_from_previous = selectedTravel;

  return itinerary;
}

// 헬퍼 함수
function addMinutes(time, minutes) {
  const [hours, mins] = time.split(':').map(Number);
  const totalMinutes = hours * 60 + mins + minutes;
  const newHours = Math.floor(totalMinutes / 60) % 24;
  const newMins = totalMinutes % 60;
  return `${String(newHours).padStart(2, '0')}:${String(newMins).padStart(2, '0')}`;
}

function subtractMinutes(time, minutes) {
  const [hours, mins] = time.split(':').map(Number);
  const totalMinutes = hours * 60 + mins - minutes;
  const newHours = ((Math.floor(totalMinutes / 60) % 24) + 24) % 24;
  const newMins = ((totalMinutes % 60) + 60) % 60;
  return `${String(newHours).padStart(2, '0')}:${String(newMins).padStart(2, '0')}`;
}
```

### 3️⃣ 호텔 변경 (⭐ 인증 필수)

```javascript
async function changeHotel(currentPlan, newHotel) {
  const userId = localStorage.getItem('userId');
  if (!userId) {
    throw new Error("로그인이 필요합니다.");
  }

  const allPlaces = extractAllPlaces(currentPlan);
  const nonHotels = allPlaces.filter(p => p.type !== "숙박");

  // ⭐ userId를 함께 전달
  const response = await apiRequest(
    "/travel/plans/update-hotel",
    "POST",
    {
      destination: currentPlan.destination,
      travel_styles: currentPlan.travel_styles,
      duration_days: currentPlan.duration_days,
      budget: currentPlan.budget,
      selected_places: nonHotels,
      new_hotel: newHotel,
      requirements: currentPlan.requirements
    },
    userId  // ← userId 추가
  );

  return response.data;
}

function extractAllPlaces(plan) {
  const places = [];
  for (const day of plan.itinerary) {
    for (const item of day.schedule) {
      places.push(item.place);
    }
  }
  return places;
}
```

### 4️⃣ 장소 교체 (⭐ 인증 필수)

```javascript
async function replacePlace(currentPlan, dayIndex, oldPlace, newPlace) {
  const userId = localStorage.getItem('userId');
  if (!userId) {
    throw new Error("로그인이 필요합니다.");
  }

  const day = currentPlan.itinerary[dayIndex];
  const allPlaces = extractAllPlaces(currentPlan);

  // ⭐ userId를 함께 전달
  const response = await apiRequest(
    "/travel/plans/replace-place",
    "POST",
    {
      day: dayIndex + 1,
      old_place: oldPlace,
      new_place: newPlace,
      all_places: allPlaces,
      destination: currentPlan.destination,
      travel_styles: currentPlan.travel_styles,
      duration_days: currentPlan.duration_days,
      budget: currentPlan.budget,
      requirements: currentPlan.requirements
    },
    userId  // ← userId 추가
  );

  return response.data;
}
```

---

## 에러 처리

### API 에러 처리

```javascript
async function apiRequest(endpoint, method = "GET", data = null) {
  try {
    const options = {
      method,
      headers: { "Content-Type": "application/json" },
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(`http://localhost:8000${endpoint}`, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API 요청 실패:", error.message);
    throw error;
  }
}
```

### 사용 예

```javascript
try {
  const plan = await generateTravelPlan({
    destination: "서울",
    startDate: "2025-12-20",
    travelStyles: ["자연"],
    durationDays: 3,
    budget: "150만원",
    requirements: []
  });
  
  displayPlan(plan);
} catch (error) {
  showErrorMessage(`여행 계획 생성 실패: ${error.message}`);
}
```

---

## React 예제

### 기본 구조 (⭐ 로그인 포함)

```jsx
import React, { useState, useCallback, useEffect } from "react";
import "./TravelPlanner.css";

const TravelPlanner = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);
  const [plan, setPlan] = useState(null);
  const [savedPlans, setSavedPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    destination: "서울",
    travelStyles: ["자연"],
    durationDays: 2,
    budget: "100만원",
    requirements: [],
  });

  // 페이지 로드 시 로그인 상태 확인
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    const user = localStorage.getItem('userId');
    if (token && user) {
      setIsLoggedIn(true);
      setUserId(user);
      loadSavedPlans(user);
    }
  }, []);

  // 저장된 플랜 로드
  const loadSavedPlans = useCallback(async (user) => {
    try {
      const response = await fetch("http://localhost:8000/travel/plans", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": user,  // ⭐ 필수 헤더
        },
      });

      if (!response.ok) throw new Error("플랜 조회 실패");
      const data = await response.json();
      setSavedPlans(data.plans || []);
    } catch (err) {
      console.error("플랜 조회 실패:", err);
    }
  }, []);

  // 여행 계획 생성
  const generatePlan = useCallback(async () => {
    if (!userId) {
      setError("로그인이 필요합니다.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/travel/plans", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,  // ⭐ 필수 헤더
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("계획 생성 실패");
      const data = await response.json();
      setPlan(data.data);
      
      // 저장된 플랜 목록 새로고침
      loadSavedPlans(userId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [formData, userId, loadSavedPlans]);

  // 로그아웃
  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userId');
    setIsLoggedIn(false);
    setUserId(null);
    setPlan(null);
    setSavedPlans([]);
  };

  // 저장된 플랜 선택
  const loadPlan = async (planId) => {
    try {
      const response = await fetch(`http://localhost:8000/travel/plans/${planId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,  // ⭐ 필수 헤더
        },
      });

      if (!response.ok) throw new Error("플랜 조회 실패");
      const data = await response.json();
      setPlan(data.plan_data);
    } catch (err) {
      setError(err.message);
    }
  };

  if (!isLoggedIn) {
    return (
      <div className="login-section">
        <h2>여행 플래너</h2>
        <p>카카오로 로그인하여 시작하세요</p>
        <a href="https://gallemalle-auth-service.politebeach-e8d743e5.eastus2.azurecontainerapps.io/login">
          <button>카카오로 로그인</button>
        </a>
      </div>
    );
  }

  return (
    <div className="travel-planner">
      <div className="header">
        <h1>여행 플래너</h1>
        <div className="user-info">
          <span>사용자 ID: {userId}</span>
          <button onClick={handleLogout}>로그아웃</button>
        </div>
      </div>

      <div className="form-section">
        <h2>새 여행 계획 생성</h2>
        <button onClick={generatePlan} disabled={loading}>
          {loading ? "생성 중..." : "계획 생성"}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

      {savedPlans.length > 0 && (
        <div className="saved-plans-section">
          <h2>저장된 플랜</h2>
          <div className="plans-list">
            {savedPlans.map((p) => (
              <div key={p.plan_id} className="plan-card">
                <h3>{p.destination}</h3>
                <p>{p.duration_days}일</p>
                <button onClick={() => loadPlan(p.plan_id)}>보기</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {plan && (
        <div className="itinerary-section">
          <h2>{plan.destination} 여행 일정</h2>
          {plan.itinerary.map((day) => (
            <DayCard key={day.day} day={day} />
          ))}
        </div>
      )}
    </div>
  );
};

const DayCard = ({ day }) => {
  return (
    <div className="day-card">
      <h3>Day {day.day}</h3>
      <div className="schedule">
        {day.schedule.map((item, idx) => (
          <ScheduleItem key={idx} item={item} />
        ))}
      </div>
    </div>
  );
};

const ScheduleItem = ({ item }) => {
  const [selectedMode, setSelectedMode] = useState("walk");

  return (
    <div className="schedule-item">
      <h4>{item.place?.name || item.name || "N/A"}</h4>
      <p className="time">
        {item.start_time} - {item.end_time}
      </p>

      {item.travel_from_previous && (
        <div className="travel-info">
          <p className="default-travel">
            기본: {item.travel_from_previous.mode}{" "}
            {item.travel_from_previous.time_minutes}분
          </p>

          {item.travel_options && (
            <div className="transport-options">
              {Object.entries(item.travel_options).map(([mode, info]) => (
                <button
                  key={mode}
                  className={selectedMode === mode ? "active" : ""}
                  onClick={() => setSelectedMode(mode)}
                >
                  {mode} ({info.time_minutes}분)
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TravelPlanner;
```

### CSS 스타일

```css
.travel-planner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
}

/* 로그인 섹션 */
.login-section {
  text-align: center;
  margin-top: 50px;
}

.login-section button {
  background: #fee500;
  color: #000;
  border: none;
  padding: 15px 30px;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}

.login-section button:hover {
  opacity: 0.9;
}

/* 헤더 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #ddd;
}

.user-info {
  display: flex;
  gap: 15px;
  align-items: center;
}

.user-info button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.user-info button:hover {
  background: #c82333;
}

/* 저장된 플랜 */
.saved-plans-section {
  margin-bottom: 30px;
}

.plans-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.plan-card {
  background: #f0f0f0;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.plan-card button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.plan-card button:hover {
  background: #0056b3;
}

.form-section {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.form-section button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.form-section button:hover {
  background: #0056b3;
}

.form-section button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #d32f2f;
  margin-top: 10px;
}

.itinerary-section {
  margin-top: 30px;
}

.day-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.day-card h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.schedule-item {
  background: #f9f9f9;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.schedule-item h4 {
  margin: 0 0 5px 0;
  color: #333;
}

.schedule-item .time {
  color: #666;
  font-size: 14px;
  margin: 5px 0;
}

.travel-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

.transport-options {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.transport-options button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.transport-options button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
```

---

## Vue.js 예제

### 기본 구조

```vue
<template>
  <div class="travel-planner">
    <div class="form-section">
      <h2>여행 계획 생성</h2>
      
      <div class="form-group">
        <label>목적지</label>
        <select v-model="formData.destination">
          <option value="서울">서울</option>
          <option value="제주도">제주도</option>
          <option value="부산">부산</option>
        </select>
      </div>

      <div class="form-group">
        <label>여행 스타일</label>
        <div class="checkbox-group">
          <label>
            <input
              type="checkbox"
              value="자연"
              v-model="formData.travelStyles"
            />
            자연
          </label>
          <label>
            <input
              type="checkbox"
              value="음식"
              v-model="formData.travelStyles"
            />
            음식
          </label>
          <label>
            <input
              type="checkbox"
              value="관광"
              v-model="formData.travelStyles"
            />
            관광
          </label>
        </div>
      </div>

      <button @click="generatePlan" :disabled="loading">
        {{ loading ? "생성 중..." : "계획 생성" }}
      </button>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="plan" class="itinerary-section">
      <h2>{{ plan.destination }} 여행 일정</h2>
      
      <div v-for="day in plan.itinerary" :key="day.day" class="day-card">
        <h3>Day {{ day.day }}</h3>
        
        <div
          v-for="(item, idx) in day.schedule"
          :key="idx"
          class="schedule-item"
        >
          <h4>{{ item.place.name }}</h4>
          <p class="time">{{ item.start_time }} - {{ item.end_time }}</p>

          <div v-if="item.travel_from_previous" class="travel-info">
            <p class="default-travel">
              기본: {{ item.travel_from_previous.mode }}
              {{ item.travel_from_previous.time_minutes }}분
            </p>

            <div v-if="item.travel_options" class="transport-options">
              <button
                v-for="(info, mode) in item.travel_options"
                :key="mode"
                :class="{ active: selectedMode[`${day.day}-${idx}`] === mode }"
                @click="selectTransport(day.day, idx, mode)"
              >
                {{ mode }} ({{ info.time_minutes }}분)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      formData: {
        destination: "서울",
        travelStyles: ["자연"],
        durationDays: 2,
        budget: "100만원",
        requirements: [],
      },
      plan: null,
      loading: false,
      error: null,
      selectedMode: {},
    };
  },
  methods: {
    async generatePlan() {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch("http://localhost:8000/travel/plans", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.formData),
        });

        if (!response.ok) throw new Error("계획 생성 실패");
        const data = await response.json();
        this.plan = data.data;
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    selectTransport(day, itemIdx, mode) {
      this.$set(this.selectedMode, `${day}-${itemIdx}`, mode);
      // 시간 업데이트 로직
    },
  },
};
</script>

<style scoped>
.travel-planner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
}

.form-section {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.checkbox-group {
  display: flex;
  gap: 15px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 0;
  width: auto;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background: #0056b3;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #d32f2f;
  margin-top: 10px;
}

.itinerary-section {
  margin-top: 30px;
}

.day-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.day-card h3 {
  margin: 0 0 15px 0;
  color: #333;
}

.schedule-item {
  background: #f9f9f9;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 4px;
  border-left: 4px solid #007bff;
}

.schedule-item h4 {
  margin: 0 0 5px 0;
  color: #333;
}

.schedule-item .time {
  color: #666;
  font-size: 14px;
  margin: 5px 0;
}

.travel-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

.transport-options {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.transport-options button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  color: #333;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.transport-options button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
</style>
```

---

## 데이터 흐름도

```
┌─────────────────┐
│  프론트엔드      │
│  (사용자 입력)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ GET /travel/destinations │
│ GET /travel/types       │
└────────┬────────────────┘
         │
         ▼
┌────────────────────────┐
│ POST /travel/plans      │
│ (여행 계획 생성)       │
└────────┬───────────────┘
         │
         ▼
┌──────────────────┐
│ Itinerary 수신   │
│ (일정 표시)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ 사용자 상호작용           │
├──────────────────────────┤
│ 1. 교통수단 변경         │ (프론트엔드에서만 처리)
│ 2. 호텔 변경              │ → /travel/plans/update-hotel
│ 3. 장소 교체              │ → /travel/plans/replace-place
└──────────────────────────┘
```

---

## 주요 팁

### 1. 성능 최적화

```javascript
// ❌ 나쁜 예: 매번 새로운 요청
const plans = [];
for (let i = 0; i < 5; i++) {
  plans.push(await generatePlan(data));
}

// ✅ 좋은 예: 병렬 요청
const plans = await Promise.all([
  generatePlan(data1),
  generatePlan(data2),
  generatePlan(data3),
]);
```

### 2. 캐싱 활용

```javascript
const planCache = {};

async function getCachedPlan(key) {
  if (planCache[key]) {
    return planCache[key];
  }

  const plan = await generatePlan(key);
  planCache[key] = plan;
  return plan;
}
```

### 3. 시간 표시 형식

```javascript
function formatDuration(minutes) {
  if (minutes < 60) return `${minutes}분`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}시간 ${mins}분`;
}
```

---

**Happy Coding! 🎉**

