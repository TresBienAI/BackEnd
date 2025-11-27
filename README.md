# LangGraph Agent API

LangGraph 기반 AI 채팅 API - 수학 연산 툴 지원

## 프로젝트 구조

```
new_project/
├── server.py              # FastAPI 메인 서버
├── tools.py               # LangGraph 툴 정의
├── routers/               # API 엔드포인트
│   └── chat.py
├── services/              # 비즈니스 로직
│   └── langgraph_service.py
├── schemas/               # 요청/응답 모델
│   └── chat.py
├── .env                   # 환경 변수
└── pyproject.toml         # 프로젝트 설정
```

## 설치 및 실행

```bash
# venv 활성화
source .venv/bin/activate

# 서버 실행
python server.py
```

서버 주소: http://localhost:8000

## API 문서

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### POST /chat/
채팅 메시지 처리

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "1과 5를 더해줘",
    "thread_id": "user-123",
    "user_id": "test-user"
  }'
```
