import uuid
import logging
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.api.telemetry import setup_telemetry
setup_telemetry()

from backend.src.graph.workflow import app as comliance_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-server")

app = FastAPI(
    title = "Azure Compliance Orchestration API",
    description = "API for video compliance against brand guidelines using Azure Video Indexer and Azure OpenAI",
    version = "1.0.0"
)

class AuditRequest(BaseModel):
    '''
    Define the expected structure of upcoming API requests.
    '''
    video_url : str

class ComplianceIssue(BaseModel):
    category: str
    description: str
    severity: str

class AuditResponse(BaseModel):
    session_id: str
    video_id : str
    status : str
    final_report : str
    compliance_issues : List[ComplianceIssue] 

@app.post("/audit", response_model=AuditResponse)
async def audit_video(request: AuditRequest):
    '''
    API Endpoint to receive video audit requests. It triggers the compliance workflow and returns the results.
    '''
    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id}"
    logger.info(f"Received audit request for video: {request.video_url} | Session ID: {session_id}")

    initial_input = {
        'video_url': request.video_url,
        'video_id': video_id_short,
        'compliance_result': [],
        'errors':[]
    }
    try:
        final_state = comliance_graph.invoke(initial_input)
        return AuditResponse(
            session_id = session_id,
            video_id= final_state.get("video_id"),
            status = final_state.get("final_status","UNKNOWN"),
            final_report = final_state.get("final_report","No Report Generated"),
            compliance_issues = final_state.get("compliance_result", [])
        )
    except Exception as e:
        logger.error(f"Error during compliance audit: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance audit failed: {str(e)}")
    
@app.get("/health")
async def health_check():
    '''
    Simple health check endpoint to verify API is running.
    '''
    return {"status": "API is healthy and running!"}
    