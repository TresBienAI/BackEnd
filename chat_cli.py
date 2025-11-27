"""
CLI 채팅 인터페이스 - 여행 플래너 테스트용
"""
import asyncio
from services.travel_service import TravelPlanService


async def main():
    print("=" * 60)
    print("🌍 여행 플래너 챗봇에 오신 것을 환영합니다!")
    print("=" * 60)
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
    
    # 서비스 초기화
    service = TravelPlanService()
    
    # 사용자 정보
    user_id = input("사용자 ID를 입력하세요 (Enter: 기본값 'user1'): ").strip() or "user1"
    thread_id = f"{user_id}-cli-chat"
    
    print(f"\n✅ 세션 시작: {thread_id}")
    print("💬 AI: 안녕하세요! 여행 계획을 도와드릴게요. 어디로 여행 가고 싶으신가요?\n")
    
    # 대화 루프
    while True:
        # 사용자 입력
        user_input = input("👤 You: ").strip()
        
        # 종료 명령
        if user_input.lower() in ['quit', 'exit', '종료', '나가기']:
            print("\n👋 여행 플래너를 종료합니다. 좋은 여행 되세요!")
            break
        
        # 빈 입력 무시
        if not user_input:
            continue
        
        try:
            # 서비스 호출
            result = await service.process_conversation(
                message=user_input,
                thread_id=thread_id,
                user_id=user_id
            )
            
            # AI 응답 출력
            print(f"\n💬 AI: {result['response']}\n")
            
            # 완료 여부 확인
            if result.get('is_completed'):
                print("=" * 60)
                print("✅ 여행 계획이 완성되었습니다!")
                print("=" * 60)
                
                # 계속할지 물어보기
                continue_chat = input("\n새로운 여행을 계획하시겠습니까? (y/n): ").strip().lower()
                if continue_chat != 'y':
                    print("\n👋 여행 플래너를 종료합니다. 좋은 여행 되세요!")
                    break
                else:
                    # 새 세션 시작
                    thread_id = f"{user_id}-cli-chat-{asyncio.get_event_loop().time()}"
                    print(f"\n✅ 새 세션 시작: {thread_id}")
                    print("💬 AI: 새로운 여행을 계획해볼까요? 어디로 가고 싶으신가요?\n")
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}\n")
            print("다시 시도해주세요.\n")


if __name__ == "__main__":
    asyncio.run(main())
