# 1단계: Python 공식 이미지 사용
FROM python:3.11-slim

# 2단계: 작업 디렉토리 설정
WORKDIR /app

# 3단계: 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4단계: pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 5단계: requirements.txt 복사 및 패키지 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6단계: 프로젝트 파일 복사
COPY . /app/

# 7단계: 포트 노출
EXPOSE 80

# 8단계: 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 9단계: 서버 실행
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]

