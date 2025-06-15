#!/usr/bin/env python3
"""
인테리어 에이전트 시스템 통합 실행 스크립트
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def install_requirements():
    """필요한 패키지 설치"""
    print("📦 패키지 설치 중...")
    
    # 모바일 챗봇 패키지
    chatbot_req = Path("mobile_chatbot/requirements.txt")
    if chatbot_req.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(chatbot_req)])
    
    # 기존 requirements.txt (FastAPI 서버용)
    if Path("requirements_fastapi.txt").exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_fastapi.txt"])
    
    print("✅ 패키지 설치 완료")

def start_fastapi_server():
    """FastAPI 서버 시작"""
    print("🚀 FastAPI 서버 시작 중...")
    return subprocess.Popen([
        sys.executable, "simple_api_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_streamlit_app():
    """Streamlit 앱 시작"""
    print("🎨 모바일 챗봇 UI 시작 중...")
    return subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "mobile_chatbot/main.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def cleanup_processes(processes):
    """프로세스 정리"""
    print("\n🔄 시스템 종료 중...")
    for name, process in processes.items():
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} 종료됨")
            except:
                try:
                    process.kill()
                    print(f"⚠️ {name} 강제 종료됨")
                except:
                    pass

def main():
    """메인 실행 함수"""
    print("🏠 인테리어 에이전트 시스템 시작")
    print("=" * 50)
    
    # 패키지 설치
    install_requirements()
    
    processes = {}
    
    try:
        # FastAPI 서버 시작
        fastapi_process = start_fastapi_server()
        processes["FastAPI 서버"] = fastapi_process
        
        # 서버 시작 대기
        print("⏳ 서버 초기화 대기 중...")
        time.sleep(3)
        
        # Streamlit 앱 시작
        streamlit_process = start_streamlit_app()
        processes["Streamlit 앱"] = streamlit_process
        
        print("\n" + "=" * 50)
        print("🎉 시스템 실행 완료!")
        print("📱 모바일 챗봇: http://localhost:8501")
        print("🌐 API 서버: http://localhost:8505")
        print("📖 API 문서: http://localhost:8505/docs")
        print("=" * 50)
        print("종료하려면 Ctrl+C를 누르세요")
        
        # 무한 대기
        while True:
            time.sleep(1)
            
            # 프로세스 상태 확인
            for name, process in processes.items():
                if process and process.poll() is not None:
                    print(f"⚠️ {name}가 종료되었습니다")
                    return
                        
    except KeyboardInterrupt:
        print("\n👋 사용자가 종료를 요청했습니다")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        cleanup_processes(processes)
        print("🏁 시스템 종료 완료")

if __name__ == "__main__":
    main() 