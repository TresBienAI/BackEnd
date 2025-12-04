"""
인증 관련 함수들
"""
from fastapi import Header, HTTPException, status
from typing import Optional


async def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """
    X-User-ID 헤더에서 사용자 ID 추출
    
    인증 서버에서 X-User-ID 헤더를 추가해서 보낸 요청에서 사용자 ID를 추출합니다.
    
    Args:
        x_user_id: HTTP 헤더의 X-User-ID 값
    
    Returns:
        user_id: 사용자 고유 ID
    
    Raises:
        HTTPException: X-User-ID 헤더가 없으면 401 Unauthorized 반환
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증되지 않은 요청입니다. X-User-ID 헤더가 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return x_user_id

