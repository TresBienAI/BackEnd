"""
FastAPI Server - LangGraph 기반 여행 플랜 API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, travel
import uvicorn

# FastAPI 앱 생성
app = FastAPI(
    title="Travel Planner API",
    description="LangGraph 기반 여행 플랜 생성 API - 맞춤형 여행 장소 추천",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Router 등록
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(travel.router, prefix="/travel", tags=["travel"])


@app.get("/", tags=["root"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Travel Planner API - 맞춤형 여행 플랜 생성!!!!!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "travel_plan": "/travel/plan",
            "destinations": "/travel/destinations",
            "types": "/travel/types"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )