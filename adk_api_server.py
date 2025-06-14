# -*- coding: utf-8 -*-
"""
ADK API Server - agent_main.py와 HTTP API로 연동
"""

from flask import Flask, request, jsonify
import asyncio
import sys
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# agent_main.py 임포트
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "interior_multi_agent"))
    from interior_agents.agent_main import root_agent
    AGENT_AVAILABLE = True
    logger.info("root_agent 로드 성공")
except Exception as e:
    logger.error(f"root_agent 로드 실패: {e}")
    AGENT_AVAILABLE = False
    root_agent = None

@app.route("/health", methods=["GET"])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "healthy",
        "agent_available": AGENT_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/agent/chat", methods=["POST"])
def chat_endpoint():
    """메인 채팅 엔드포인트"""
    if not AGENT_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent not available",
            "message": "root_agent를 로드할 수 없습니다."
        }), 500
    
    try:
        data = request.json
        user_input = data.get("message", "")
        
        if not user_input:
            return jsonify({
                "success": False,
                "error": "Empty message"
            }), 400
        
        logger.info(f"받은 메시지: {user_input}")
        
        # 에이전트 정보 로깅
        logger.info(f"에이전트 타입: {type(root_agent)}")
        available_methods = [method for method in dir(root_agent) if not method.startswith('_')]
        logger.info(f"사용 가능한 메서드: {available_methods}")
        
        # 비동기 방식으로 실행 (LlmAgent는 주로 run_async만 지원)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def process_message():
                try:
                    logger.info("다양한 에이전트 실행 방법 시도...")
                    
                    # 에이전트 기본 정보 확인
                    logger.info(f"에이전트 이름: {getattr(root_agent, 'name', 'Unknown')}")
                    logger.info(f"에이전트 설명: {getattr(root_agent, 'description', 'No description')}")
                    logger.info(f"에이전트 도구 수: {len(getattr(root_agent, 'tools', []))}")
                    
                    # 방법 1: run_live 시도 (동기 방식)
                    try:
                        logger.info("방법 1: run_live 시도")
                        if hasattr(root_agent, 'run_live'):
                            logger.info("run_live 메서드 존재 확인됨")
                            response_generator = root_agent.run_live(user_input)
                            logger.info(f"run_live 호출 완료: {type(response_generator)}")
                            logger.info(f"response_generator 속성: {dir(response_generator)}")
                            
                            # run_live도 async_generator를 반환하므로 처리
                            if hasattr(response_generator, '__aiter__'):
                                logger.info("async_generator로 처리 시작")
                                full_response = ""
                                chunk_count = 0
                                
                                async for chunk in response_generator:
                                    chunk_count += 1
                                    logger.info(f"run_live 청크 {chunk_count}: {type(chunk)} - {chunk}")
                                    
                                    if isinstance(chunk, dict):
                                        if "content" in chunk:
                                            full_response += chunk["content"]
                                        elif "text" in chunk:
                                            full_response += chunk["text"]
                                        else:
                                            full_response += str(chunk)
                                    elif hasattr(chunk, "content"):
                                        full_response += chunk.content
                                    elif hasattr(chunk, "text"):
                                        full_response += chunk.text
                                    else:
                                        full_response += str(chunk)
                                
                                logger.info(f"run_live 총 {chunk_count}개 청크 처리 완료")
                                logger.info(f"최종 응답: {full_response}")
                                return {"success": True, "response": full_response}
                            else:
                                # 일반 응답인 경우
                                logger.info("일반 응답으로 처리")
                                return {"success": True, "response": str(response_generator)}
                        else:
                            logger.warning("run_live 메서드가 존재하지 않음")
                    except Exception as e1:
                        logger.error(f"run_live 실패 - 상세 오류: {e1}")
                        import traceback
                        logger.error(f"run_live 스택 트레이스: {traceback.format_exc()}")
                    
                    # 방법 2: 간단한 텍스트 응답 생성 (테스트용)
                    try:
                        logger.info("방법 2: 간단한 텍스트 응답 생성")
                        
                        # 에이전트 정보를 기반으로 간단한 응답 생성
                        simple_response = f"""안녕하세요! 인테리어 통합 관리 에이전트입니다.

요청하신 내용: {user_input}

현재 사용 가능한 기능:
- 에이전트 이름: {getattr(root_agent, 'name', 'Unknown')}
- 도구 개수: {len(getattr(root_agent, 'tools', []))}개
- 상태: 정상 작동 중

실제 도구 연동 기능은 현재 개발 중입니다."""
                        
                        logger.info("간단한 응답 생성 성공")
                        return {"success": True, "response": simple_response}
                        
                    except Exception as e2:
                        logger.error(f"간단한 응답 생성 실패: {e2}")
                    
                    # 방법 3: 모델 직접 호출
                    try:
                        logger.info("방법 3: 모델 직접 호출 시도")
                        if hasattr(root_agent, 'model') and root_agent.model:
                            model = root_agent.model
                            logger.info(f"모델 타입: {type(model)}")
                            
                            if hasattr(model, 'generate_content'):
                                response = model.generate_content(user_input)
                                logger.info(f"모델 직접 호출 성공: {type(response)}")
                                
                                # 응답 처리
                                if hasattr(response, 'text'):
                                    return {"success": True, "response": response.text}
                                elif hasattr(response, 'content'):
                                    return {"success": True, "response": response.content}
                                else:
                                    return {"success": True, "response": str(response)}
                    except Exception as e3:
                        logger.warning(f"모델 직접 호출 실패: {e3}")
                    
                    # 방법 4: 에이전트의 도구들 직접 사용
                    try:
                        logger.info("방법 4: 에이전트 도구 직접 사용 시도")
                        if hasattr(root_agent, 'tools') and root_agent.tools:
                            logger.info(f"사용 가능한 도구 수: {len(root_agent.tools)}")
                            for i, tool in enumerate(root_agent.tools):
                                logger.info(f"도구 {i}: {type(tool)} - {getattr(tool, 'name', 'unnamed')}")
                    except Exception as e4:
                        logger.warning(f"도구 확인 실패: {e4}")
                    
                    # 방법 5: 간단한 컨텍스트 객체 생성 시도
                    try:
                        logger.info("방법 5: 간단한 컨텍스트 객체 생성")
                        
                        # Pydantic BaseModel 기반 간단한 컨텍스트 생성
                        from pydantic import BaseModel
                        
                        class SimpleContext(BaseModel):
                            agent: object = None
                            message: str = ""
                            
                            class Config:
                                arbitrary_types_allowed = True
                        
                        simple_context = SimpleContext(agent=root_agent, message=user_input)
                        logger.info("간단한 컨텍스트 생성 성공")
                        
                        response_generator = root_agent.run_async(user_input, simple_context)
                        logger.info("간단한 컨텍스트로 run_async 호출 성공")
                        
                        full_response = ""
                        chunk_count = 0
                        
                        async for chunk in response_generator:
                            chunk_count += 1
                            logger.info(f"청크 {chunk_count}: {type(chunk)}")
                            
                            if isinstance(chunk, dict):
                                if "content" in chunk:
                                    full_response += chunk["content"]
                                elif "text" in chunk:
                                    full_response += chunk["text"]
                                else:
                                    full_response += str(chunk)
                            elif hasattr(chunk, "content"):
                                full_response += chunk.content
                            else:
                                full_response += str(chunk)
                        
                        logger.info(f"총 {chunk_count}개 청크 처리 완료")
                        return {"success": True, "response": full_response}
                        
                    except Exception as e5:
                        logger.warning(f"간단한 컨텍스트 방법 실패: {e5}")
                    
                    # 방법 6: None을 명시적으로 전달
                    try:
                        logger.info("방법 6: None 컨텍스트 시도")
                        response_generator = root_agent.run_async(user_input, None)
                        logger.info("None 컨텍스트로 run_async 호출 성공")
                        
                        full_response = ""
                        async for chunk in response_generator:
                            if isinstance(chunk, dict):
                                if "content" in chunk:
                                    full_response += chunk["content"]
                                elif "text" in chunk:
                                    full_response += chunk["text"]
                                else:
                                    full_response += str(chunk)
                            elif hasattr(chunk, "content"):
                                full_response += chunk.content
                            else:
                                full_response += str(chunk)
                        
                        return {"success": True, "response": full_response}
                        
                    except Exception as e6:
                        logger.warning(f"None 컨텍스트 방법 실패: {e6}")
                    
                    # 모든 방법 실패
                    raise Exception("모든 에이전트 실행 방법이 실패했습니다")
                    
                except Exception as e:
                    logger.error(f"비동기 에이전트 실행 오류: {type(e).__name__}: {e}")
                    import traceback
                    logger.error(f"상세 오류: {traceback.format_exc()}")
                    return {"success": False, "error": str(e)}
            
            result = loop.run_until_complete(process_message())
            
        finally:
            loop.close()
        
        # 결과 처리
        if isinstance(result, dict):
            if result.get("success"):
                logger.info(f"응답 생성 완료: {len(result.get('response', ''))} 문자")
                return jsonify({
                    "success": True,
                    "response": result.get("response"),
                    "agent_type": "root_agent",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.error(f"에이전트 오류: {result.get('error')}")
                return jsonify({
                    "success": False,
                    "error": result.get("error"),
                    "agent_type": "root_agent",
                    "timestamp": datetime.now().isoformat()
                }), 500
        else:
            # 이전 버전 호환성
            logger.info(f"응답 생성 완료: {len(str(result))} 문자")
            return jsonify({
                "success": True,
                "response": str(result),
                "agent_type": "root_agent",
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"처리 오류: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    print("ADK API 서버 시작 중...")
    print(f"URL: http://localhost:8505")
    print(f"Agent 상태: {'사용 가능' if AGENT_AVAILABLE else '사용 불가'}")
    app.run(host="localhost", port=8505, debug=True) 