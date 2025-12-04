"""
State Schema - LangGraph 상태 정의
"""
from langgraph.graph import MessagesState
from typing import Optional


class TravelState(MessagesState):
    """여행 플랜 생성을 위한 상태 (Slot Filling)"""
    destination: Optional[str]
    start_date: Optional[str]
    duration: Optional[str]
    people: Optional[str]
    budget: Optional[str]
    travel_type: Optional[str]
    requirements: Optional[str]
