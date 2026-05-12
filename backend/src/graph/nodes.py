import json
import os
import logging
import re
from typing import Dict,Any,List

from langchain_openai import AzureChatOpenAI,AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from backend.src.graph.state import VideoAuditState,ComplianceIssue

from backend.src.services.video_indexer import VideoIndexerService

logger = logging.getLogger("brand-guardian")
logging.basicConfig(level = logging.INFO)

def index_video_node(state:VideoAuditState) -> Dict[str,Any]:
    """
    Download the yt video from url 
    Uploads to Azure Video indexer
    Extract the insights
    """

    video_url = state.get("video_url")
    video_id_input = state.get("video_id","vid_demo")

    logger.info(f"-------------------[Node:Indexer] Processing: {video_url}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()
        #download
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path = local_filename)

        else:
            raise Exception("Please provide a valid youtube url.")
        
        azure_video_id = vi_service.upload_video(local_path, video_name = video_id_input)
        logger.info(f"Upload Success. Azure ID : {azure_video_id}")

        if os.path.exists(local_path):
            os.remove(local_path)
        
        raw_insight = vi_service.wait_for_processing(azure_video_id)

        clean_data = vi_service.extract_data(raw_insight)
        logger.info("---[NODE: Indexer] Extraction Complete ------")
        return clean_data
    
    except Exception as e:
        logger.error(f"Video Indexer Failed: {e}")
        return {
            "error" : [str(e)],
            "final" : "FAIL",
            "transcript" : "",
            "orc_text" : []
        }
    
# Node 2: Compliance Auditor
def audio_content_node(state: VideoAuditState)-> Dict[str,Any]:
    """Performs Retrieval Aumented Generation to audit the content - brand Video

    Args:
        state (VideoAuditState): _description_

    Returns:
        Dict[str,Any]: _description_
    """

    logger.info("---[Node: Auditor] quering Knowledge base & LLM")
    transcript = state.get("transcript","")
    if not transcript:
        logger.info("No Transcript available. Skipping audit......")
        return {
            "final_status" : "FAIL",
            "final_report" : "Audit Skipped because the video processing failed(No Transcript)"
        }
    
    llm = AzureChatOpenAI(
        azure_deployment= os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature =0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-small",
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    )

    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function = embeddings.embed_query
    )

    ocr_text = state.get("ocr_text",[])
    query_text = f"{transcript} {''.join(ocr_text)}"
    docs = vector_store.similarity_search(query_text, k=3)
    retireved_rules = "\n\n".join([doc.page_content for doc in docs])


    system_prompts = f"""
You are a senior brand compliance auditor.
OFFICIAL REGULATORY RULES:
{retireved_rules}
INSTRUCTION:
1. Analyze the trancript and oct text below.
2. Identify ANY violations of the rules.
3. Return strictly JSON in the following format:
 {{
        "compliance_results": [
            {{
                "category": "Claim Validation",
                "severity": "CRITICAL",
                "description": "Explanation of the violation..."
            }}
        ],
        "status": "FAIL", 
        "final_report": "Summary of findings..."
    }}

If no violations are found, set "status" to "PASS" and "compliance_results" to [].
"""
    
    user_message = f"""
VIDEO_METADATA: {state.get("video_metadata",{})}
TRANSCRIPT: {transcript}
OCR_TEXT: {ocr_text}
"""
    try:
        response = llm.invoke(
            [SystemMessage(content=system_prompts),
              HumanMessage(content=user_message)])
        content = response.content
        if "```" in content:
            content = re.search(r"```json(.*?)```", content, re.DOTALL).group(1)
        audit_data = json.loads(content.strip())
        return {
            "compliance_results" : audit_data.get("compliance_results",[]),
            "final_status" : audit_data.get("status","FAIL"),
            "final_report" : audit_data.get("final_report","No report generated.")
        }
    except Exception as e:
        logger.error(f"System Error in auditor node: {e}")
        logger.error(f"Raw LLM Response: {response.content if 'response' in locals() else 'No response'}")
        return {
            "compliance_results" : [],
            "final_status" : "FAIL",
            "final_report" : f"Audit Failed due to system error: {str(e)}"
        }