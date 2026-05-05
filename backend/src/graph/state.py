import operator
from typing import Annotated, List, Dict, Optional, Any, TypedDict

# define the schema for a single compliance result 
class ComplianceIssue(TypedDict):
    category : str
    description : str
    severity : str
    timestamp : Optional[str]

# define the global graph state
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langgraph execution content
    '''
    # input parameters
    video_url : str
    video_id : str

    # ingestion and extraction data
    local_file_path : Optional[str]
    video_metadata: Dict[str,any]
    transcript : Optional[str]
    ocr_text : List[str]

    #analysis output, stores the list of all the violations found by AI
    compliance_results: Annotated[List[ComplianceIssue],operator.add]

    #final deliverable
    final_status : str
    final_report : str

    #system observability
    errors: Annotated[List[str], operator.add]
