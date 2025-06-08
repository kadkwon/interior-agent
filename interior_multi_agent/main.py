from fastapi import FastAPI, HTTPException
from google.adk.agents import WorkflowAgent
import uvicorn

from config.settings import APP_TITLE, APP_DESCRIPTION, APP_VERSION, HOST, PORT
from agents.site_agent import site_agent

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

# 메인 Workflow Agent
main_agent = WorkflowAgent(
    name="interior_manager",
    description="인테리어 프로젝트의 전체 조정을 담당하는 메인 Agent",
    agents=[site_agent],
    routing_strategy="llm"
)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Interior Management System is running",
        "version": APP_VERSION
    }

@app.post("/process")
async def process_request(request: dict):
    try:
        response = await main_agent.process(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT) 