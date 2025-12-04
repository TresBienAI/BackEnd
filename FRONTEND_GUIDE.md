# 프론트엔드 개발 가이드

프론트엔드에서 Travel Planner API를 사용하기 위한 완벽한 가이드입니다.

## 📋 목차

1. [시작하기](#시작하기)
2. [API 엔드포인트](#api-엔드포인트)
3. [데이터 구조](#데이터-구조)
4. [요청/응답 예시](#요청응답-예시)
5. [주요 기능 구현](#주요-기능-구현)
6. [에러 처리](#에러-처리)
7. [React 예제](#react-예제)
8. [Vue.js 예제](#vuejs-예제)

---

## 시작하기

### API 서버 연결

```javascript
const API_BASE_URL = "http://localhost:8000";

// 기본 요청 함수
async function apiRequest(endpoint, method = "GET", data = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return await response.json();
}
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

### 3. POST /travel/plans
여행 일정을 생성합니다.

**요청:**
```javascript
const planRequest = {
  destination: "서울",
  start_date: "2025-12-20",
  travel_styles: ["자연", "맛집"],
  duration_days: 2,
  budget: "100만원",
  requirements: [],
  include_debug: false
};

const plan = await apiRequest("/travel/plans", "POST", planRequest);
```

**응답 구조:**
```json
{
  "success": true,
  "message": "여행 일정이 성공적으로 생성되었습니다.",
  "data": {
    "destination": "서울",
    "duration_days": 2,
    "total_places": 10,
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

### 4. POST /travel/plans/update-hotel
호텔을 변경하고 일정을 재계산합니다.

**요청:**
```javascript
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

const newPlan = await apiRequest(
  "/travel/plans/update-hotel",
  "POST",
  hotelChangeRequest
);
```

---

### 5. POST /travel/plans/replace-place
특정 장소를 다른 장소로 교체합니다.

**요청:**
```javascript
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

const updatedPlan = await apiRequest(
  "/travel/plans/replace-place",
  "POST",
  replaceRequest
);
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

### 1️⃣ 여행 계획 생성

```javascript
async function generateTravelPlan(formData) {
  try {
    const response = await apiRequest("/travel/plans", "POST", {
      destination: formData.destination,
      start_date: formData.startDate,
      travel_styles: formData.travelStyles,
      duration_days: formData.durationDays,
      budget: formData.budget,
      requirements: formData.requirements,
      include_debug: false
    });

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

### 3️⃣ 호텔 변경

```javascript
async function changeHotel(currentPlan, newHotel) {
  const allPlaces = extractAllPlaces(currentPlan);
  const nonHotels = allPlaces.filter(p => p.type !== "숙박");

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
    }
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

### 4️⃣ 장소 교체

```javascript
async function replacePlace(currentPlan, dayIndex, oldPlace, newPlace) {
  const day = currentPlan.itinerary[dayIndex];
  const allPlaces = extractAllPlaces(currentPlan);

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
    }
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

### 기본 구조

```jsx
import React, { useState, useCallback } from "react";
import "./TravelPlanner.css";

const TravelPlanner = () => {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    destination: "서울",
    travelStyles: ["자연"],
    durationDays: 2,
    budget: "100만원",
    requirements: [],
  });

  const generatePlan = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/travel/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("계획 생성 실패");
      const data = await response.json();
      setPlan(data.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [formData]);

  return (
    <div className="travel-planner">
      <div className="form-section">
        <h2>여행 계획 생성</h2>
        <button onClick={generatePlan} disabled={loading}>
          {loading ? "생성 중..." : "계획 생성"}
        </button>
        {error && <div className="error">{error}</div>}
      </div>

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
      <h4>{item.place.name}</h4>
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

