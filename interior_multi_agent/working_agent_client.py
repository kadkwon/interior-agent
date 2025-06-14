#!/usr/bin/env python3
"""
정상 작동하는 Agent Engine 클라이언트
기본 stream_query 방식 사용 (세션 없음)
"""

import os
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# ADC 강제 사용
os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

def main():
    print("🎉 정상 작동하는 Agent Engine 클라이언트")
    print("gemini-2.5-flash-preview-05-20 모델 사용")
    print("=" * 60)
    
    # 기본 설정
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "interior-one-click")
    location = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
    staging_bucket = f"gs://{os.getenv('STAGING_BUCKET_NAME', 'interior-one-click-agent-staging')}"
    
    # 성공한 에이전트 리소스 ID
    resource_name = "projects/638331849453/locations/us-central1/reasoningEngines/3043421797404901376"
    
    try:
        # Vertex AI 초기화
        vertexai.init(
            project=project_id,
            location=location,
            staging_bucket=staging_bucket
        )
        
        # 에이전트 로드
        agent = agent_engines.AgentEngine(resource_name=resource_name)
        print(f"✅ 에이전트 로드: {agent.display_name}")
        print(f"📋 리소스 ID: {agent.resource_name}")
        print()
        
        print("💡 사용 가능한 명령어:")
        print("   - 주소 내역을 보여줘")
        print("   - 프로젝트 목록을 보여줘")
        print("   - 새 프로젝트를 만들어줘")
        print("   - 종료하려면 'quit' 또는 'exit' 입력")
        print()
        
        while True:
            try:
                # 사용자 입력 받기
                user_input = input("🤖 질문을 입력하세요: ").strip()
                
                if user_input.lower() in ['quit', 'exit', '종료', '나가기']:
                    print("👋 Agent Engine 클라이언트를 종료합니다.")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n📝 처리 중: {user_input}")
                print("-" * 50)
                
                # Agent Engine 실행 (기본 stream_query 방식)
                response = agent.stream_query(
                    message=user_input,
                    user_id=f"user_{hash(user_input) % 10000}"
                )
                
                response_text = ""
                chunk_count = 0
                
                print("💬 응답:")
                for chunk in response:
                    chunk_count += 1
                    
                    if isinstance(chunk, dict):
                        if 'content' in chunk and 'parts' in chunk['content']:
                            for part in chunk['content']['parts']:
                                if 'text' in part:
                                    text = part['text']
                                    print(text, end='', flush=True)
                                    response_text += text
                        elif 'text' in chunk:
                            text = chunk['text']
                            print(text, end='', flush=True)
                            response_text += text
                    elif hasattr(chunk, 'text'):
                        print(chunk.text, end='', flush=True)
                        response_text += chunk.text
                    else:
                        text = str(chunk)
                        print(text, end='', flush=True)
                        response_text += text
                
                print(f"\n\n📊 총 {chunk_count}개 청크 처리됨")
                
                if not response_text.strip():
                    print("⚠️ 빈 응답이 반환되었습니다.")
                
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\n👋 사용자가 중단했습니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                print("다시 시도해주세요.")
                
    except Exception as e:
        print(f"❌ 에이전트 로드 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 