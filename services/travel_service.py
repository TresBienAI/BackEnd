"""
Travel Service - 여행 플랜 생성을 위한 LangGraph 서비스
"""
import os
from typing import Dict, Any, Optional, List
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tools.travel_tools import travel_tools
from schemas.state import TravelState

load_dotenv()


class TravelDetails(BaseModel):
    """여행 정보 추출을 위한 모델"""
    destination: Optional[str] = Field(None, description="여행지 (예: 서울, 제주도, 부산)")
    duration: Optional[str] = Field(None, description="여행 기간 (예: 1박 2일, 3일)")
    people: Optional[str] = Field(None, description="인원 (예: 2명, 혼자)")
    budget: Optional[str] = Field(None, description="예산 (예: 10만원, 20만원)")
    travel_type: Optional[str] = Field(None, description="여행 스타일 (예: 힐링, 맛집, 액티비티)")
    requirements: Optional[str] = Field(None, description="추가 요청사항 (예: 채식주의자, 아이 동반)")


class TravelPlanService:
    """LangGraph 기반 여행 플랜 생성 서비스 (Slot Filling & One-Shot)"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_DEPLOYMENT", "gpt-4o-mini"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            api_key=os.getenv("AZURE_API_KEY")
        )
        
        # 툴 바인딩
        self.llm_with_tools = self.llm.bind_tools(travel_tools)
        
        # 정보 추출용 LLM
        self.extractor_llm = self.llm.with_structured_output(TravelDetails)
        
        # 메모리 초기화
        self.memory = MemorySaver()
        
        # 그래프 구성
        self.app = self._build_graph()
    
    def _build_graph(self):
        """LangGraph 그래프 구성"""
        graph = StateGraph(TravelState)
        
        # 노드 추가
        graph.add_node("extractor", self._extractor_node)
        graph.add_node("chatbot", self._chatbot_node)
        graph.add_node("tools", ToolNode(travel_tools))
        
        # 엣지 설정
        graph.set_entry_point("extractor")
        graph.add_edge("extractor", "chatbot")
        graph.add_conditional_edges("chatbot", tools_condition)
        graph.add_edge("tools", "chatbot")
        
        # 컴파일
        return graph.compile(checkpointer=self.memory)
    
    async def _extractor_node(self, state: TravelState):
        """대화 내용에서 여행 정보 추출"""
        messages = state["messages"]
        
        # 마지막 메시지가 사람이 쓴 것일 때만 추출 시도 (효율성)
        if isinstance(messages[-1], HumanMessage):
            extraction = await self.extractor_llm.ainvoke(messages)
            # None이 아닌 값만 업데이트
            return {k: v for k, v in extraction.dict().items() if v is not None}
        return {}

    async def _chatbot_node(self, state: TravelState):
        """챗봇 노드 - 정보 확인 및 툴 호출"""
        
        # 1. 필수 정보 확인
        required_slots = {
            "destination": "여행지",
            "duration": "여행 기간",
            "people": "인원",
            "budget": "예산",
            "travel_type": "여행 스타일"
        }
        
        missing_slots = []
        for key, label in required_slots.items():
            if not state.get(key):
                missing_slots.append(label)
        
        # 2. 마지막 메시지 확인
        last_msg = state["messages"][-1]
        
        # 3. 툴 실행 결과가 있고 + 모든 정보가 수집된 경우 -> 최종 계획 생성
        if isinstance(last_msg, ToolMessage) and not missing_slots:
            system_msg = f"""
            검색된 장소 정보를 바탕으로 여행 계획을 제안해주세요.
            
            [수집된 정보]
            - 목적지: {state.get('destination')}
            - 기간: {state.get('duration')}
            - 인원: {state.get('people')}
            - 예산: {state.get('budget')}
            - 스타일: {state.get('travel_type')}
            - 추가사항: {state.get('requirements')}
            
            [작성 가이드]
            1. 추천 장소 목록을 보여주세요.
            2. 각 장소에 대한 간단한 설명을 덧붙여주세요.
            3. 전체적인 여행 코스를 요약해주세요.
            """
            response = await self.llm.ainvoke([SystemMessage(content=system_msg)] + state["messages"])
            return {"messages": [response]}

        # 4. 정보가 부족한 경우 -> 질문하기
        elif missing_slots:
            system_msg = f"""
            당신은 친절한 여행 플래너입니다. 사용자의 여행 계획을 위해 다음 정보가 필요합니다.
            
            [현재 수집된 정보]
            - 목적지: {state.get('destination') or '(미정)'}
            - 기간: {state.get('duration') or '(미정)'}
            - 인원: {state.get('people') or '(미정)'}
            - 예산: {state.get('budget') or '(미정)'}
            - 스타일: {state.get('travel_type') or '(미정)'}
            
            [누락된 정보]
            {', '.join(missing_slots)}
            
            누락된 정보를 자연스럽게 물어보세요. 한 번에 1~2개씩 물어보는 것이 좋습니다.
            """
            response = await self.llm.ainvoke([SystemMessage(content=system_msg)] + state["messages"])
            return {"messages": [response]}
        
        # 5. 모든 정보가 수집된 경우 -> 툴 호출
        elif not missing_slots:
            system_msg = f"""
            모든 여행 정보가 수집되었습니다.
            - 목적지: {state.get('destination')}
            - 기간: {state.get('duration')}
            - 인원: {state.get('people')}
            - 예산: {state.get('budget')}
            - 스타일: {state.get('travel_type')}
            - 추가사항: {state.get('requirements') or '없음'}
            
            `search_places` 툴을 사용하여 적절한 장소를 검색하세요.
            검색 후, 위의 모든 정보(기간, 인원, 예산 등)를 고려하여 여행 계획을 세워주세요.
            """
            response = await self.llm_with_tools.ainvoke([SystemMessage(content=system_msg)] + state["messages"])
            return {"messages": [response]}

    async def process_conversation(
        self,
        message: str,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = "anonymous"
    ) -> Dict[str, Any]:
        """대화 처리 및 여행 계획 진행"""
        
        config = {
            "configurable": {
                "thread_id": thread_id or f"{user_id}-travel-chat",
                "user_id": user_id
            }
        }
        
        # LangGraph 실행
        result = await self.app.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config
        )
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        
        # 계획 생성 완료 여부 판단
        # 툴을 사용했고(히스토리에 ToolMessage 존재), 마지막이 AI 메시지인 경우 완료로 간주
        has_tool_call = any(isinstance(m, ToolMessage) for m in result["messages"])
        is_completed = has_tool_call and isinstance(last_message, AIMessage)
        
        return {
            "response": response_text,
            "thread_id": config["configurable"]["thread_id"],
            "is_completed": is_completed
        }

    async def create_travel_plan(
        self,
        destination: str,
        travel_type: str,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = "anonymous"
    ) -> Dict[str, Any]:
        """
        [One-Shot] 여행 플랜 생성
        사용자가 한 번에 정보를 입력했을 때 사용하는 메서드
        """
        # 스레드 ID 생성 (대화형과 구분)
        thread_id = thread_id or f"{user_id}-travel-plan-{destination}"
        
        # 모든 정보를 포함한 메시지 생성
        user_message = f"""
        {destination}에서 {travel_type} 여행을 계획하고 싶어.
        기간은 1박 2일, 인원은 2명, 예산은 30만원이야.
        추가 요청사항은 없어.
        바로 계획을 짜줘.
        """
        
        # 대화 처리 메서드 재사용
        result = await self.process_conversation(
            message=user_message,
            thread_id=thread_id,
            user_id=user_id
        )
        
        # 응답 포맷팅 (TravelPlanResponse 호환)
        # 실제로는 places 리스트를 추출해야 하지만, MVP에서는 텍스트 요약만 반환하거나
        # process_conversation에서 places를 추출하도록 로직을 개선해야 함.
        # 여기서는 간단히 텍스트 요약을 summary로 사용하고 places는 빈 리스트 또는 추출 로직 추가.
        
        # 장소 추출 로직 (간소화)
        places = []
        # (실제 구현 시에는 _extract_places_from_messages 같은 메서드 필요)
        
        return {
            "destination": destination,
            "travel_type": travel_type,
            "places": places, # MVP: 빈 리스트 또는 파싱 로직 필요
            "thread_id": thread_id,
            "summary": result["response"]
        }
