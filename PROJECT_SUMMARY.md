# Azure Compliance Orchestration - Detailed Project Summary

---

## 1. EXECUTIVE SUMMARY

**Project Name**: Azure Compliance Orchestration  
**Project Type**: Automated Video Compliance Audit System  
**Version**: 0.1.0  
**Status**: Development  
**Primary Language**: Python 3.13+

The Azure Compliance Orchestration system is an **intelligent video compliance auditing platform** that automatically analyzes YouTube videos against brand compliance guidelines and regulatory rules. It leverages Azure's AI services and OpenAI's GPT-4 to detect violations, providing automated quality assurance for brand video content.

---

## 2. PROBLEM STATEMENT & MOTIVATION

### Business Problem
Organizations face several challenges in video content compliance:

1. **Manual Review Overhead**: Marketing teams must manually review videos against complex compliance rules
2. **Human Error**: Inconsistent application of guidelines; subjective interpretations
3. **Scalability Issues**: Cannot efficiently audit large volumes of video content
4. **Time Delays**: Manual processes slow down content release cycles
5. **Inconsistent Standards**: Lack of standardized compliance checking methodology
6. **Regulatory Risk**: Missing violations could lead to legal, brand, or regulatory issues

### Solution Approach
Automate the compliance audit process using:
- **Video Intelligence**: Azure Video Indexer for automatic transcript and OCR extraction
- **AI-Powered Analysis**: Azure OpenAI (GPT-4) for intelligent rule matching
- **Knowledge Management**: Azure Search for semantic search of compliance rules
- **Workflow Orchestration**: LangGraph for coordinating complex multi-step audits

---

## 3. HIGH-LEVEL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT / USER                            │
│        (Web App / API / CLI Simulation)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    YouTube Video URL
                           │
         ┌─────────────────▼────────────────────┐
         │    FastAPI Server                    │
         │  (Backend API Layer)                │
         │  ┌──────────────────────────────┐   │
         │  │ /audit (POST)                │   │
         │  │ /health (GET)                │   │
         │  └──────────────────────────────┘   │
         └─────────────────┬────────────────────┘
                           │
         ┌─────────────────▼─────────────────────────────┐
         │   LANGGRAPH WORKFLOW ENGINE                   │
         │   (Orchestration & State Management)         │
         │                                              │
         │  ┌────────────────────────────────────────┐ │
         │  │   START NODE                           │ │
         │  │   ├─ Initialize State                  │ │
         │  │   └─ Validate Input                    │ │
         │  └─────────┬──────────────────────────────┘ │
         │            │                                 │
         │  ┌─────────▼──────────────────────────────┐ │
         │  │   INDEXER NODE                         │ │
         │  │   ├─ Download Video (yt-dlp)          │ │
         │  │   ├─ Upload to Azure VI                │ │
         │  │   ├─ Poll Processing Status            │ │
         │  │   └─ Extract Data (Transcript/OCR)    │ │
         │  └─────────┬──────────────────────────────┘ │
         │            │                                 │
         │  ┌─────────▼──────────────────────────────┐ │
         │  │   AUDITOR NODE                        │ │
         │  │   ├─ Query Azure Search (RAG)         │ │
         │  │   ├─ Invoke GPT-4 Analysis            │ │
         │  │   ├─ Parse Compliance Results         │ │
         │  │   └─ Generate Report                  │ │
         │  └─────────┬──────────────────────────────┘ │
         │            │                                 │
         │  ┌─────────▼──────────────────────────────┐ │
         │  │   END NODE                             │ │
         │  │   └─ Return Final State                │ │
         │  └────────────────────────────────────────┘ │
         │                                              │
         └────────────────────┬─────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────────────────┐
        │                                                       │
        │          EXTERNAL AZURE SERVICES                    │
        │                                                       │
        ├──► Azure Video Indexer                              │
        │    (Video Processing & Insight Extraction)          │
        │                                                       │
        ├──► Azure OpenAI / GPT-4                             │
        │    (Language Model for Compliance Analysis)         │
        │                                                       │
        ├──► Azure Search                                     │
        │    (Vector DB for Compliance Rules)                │
        │                                                       │
        ├──► Azure Storage (Blob)                            │
        │    (Video Storage)                                  │
        │                                                       │
        ├──► Azure Monitor / Application Insights            │
        │    (Telemetry & Observability)                     │
        │                                                       │
        └──► LangSmith                                        │
             (LLM Tracing & Monitoring)                       │
        
```

---

## 4. DETAILED COMPONENT BREAKDOWN

### 4.1 API Layer (`backend/src/api/`)

#### **server.py** - FastAPI Application
**Purpose**: REST API entry point for compliance audit requests

**Key Endpoints:**
```
POST /audit
├── Input: AuditRequest(video_url: str)
├── Processing: 
│   ├─ Generate session_id (UUID)
│   ├─ Invoke compliance workflow
│   └─ Wait for results
└── Output: AuditResponse
    ├─ session_id
    ├─ video_id
    ├─ status (PASS/FAIL/UNKNOWN)
    ├─ final_report
    └─ compliance_issues[]

GET /health
├── Purpose: Health check
└── Output: {"status": "API is healthy and running!"}
```

**Request/Response Models:**
```python
class AuditRequest:
    video_url: str  # YouTube URL to audit

class ComplianceIssue:
    category: str       # e.g., "Claim Validation", "Brand Voice"
    description: str    # Detailed violation description
    severity: str       # CRITICAL, HIGH, MEDIUM, LOW

class AuditResponse:
    session_id: str
    video_id: str
    status: str
    final_report: str
    compliance_issues: List[ComplianceIssue]
```

#### **telemetry.py** - Azure Monitor Configuration
**Purpose**: Setup observability for production monitoring

**Functions:**
- Configures OpenTelemetry SDK
- Connects to Azure Application Insights
- Logs traces, metrics, and exceptions
- Enables LangSmith integration for LLM tracing

**Configuration:**
```
- Connection String from environment
- Logger name: "azure-comp-orestration-tracing"
- Automatic instrumentation of FastAPI
```

---

### 4.2 Workflow Orchestration (`backend/src/graph/`)

#### **state.py** - Data Schema Definition
**Purpose**: Defines the immutable state structure passed through the workflow

**State Structure:**
```python
class VideoAuditState(TypedDict):
    # Input Parameters
    video_url: str                    # YouTube URL
    video_id: str                     # Unique identifier
    
    # Ingestion & Extraction
    local_file_path: Optional[str]    # Temp file path
    video_metadata: Dict              # Duration, platform, etc.
    transcript: Optional[str]         # Speech-to-text
    ocr_text: List[str]              # Text from video frames
    
    # Analysis Output (Accumulator - supports multi-agent)
    compliance_results: List[ComplianceIssue]  # All violations found
    
    # Final Deliverable
    final_status: str                 # PASS/FAIL status
    final_report: str                 # Executive summary
    
    # System Observability
    errors: List[str]                 # Error tracking
```

**Key Design Pattern:**
- `Annotated[List[X], operator.add]` enables state accumulation across workflow steps
- Immutable design ensures reproducibility and debugging

#### **workflow.py** - DAG Definition
**Purpose**: Orchestrates the directed acyclic graph (DAG) of processing steps

**Workflow Structure:**
```
START → [Indexer Node] → [Auditor Node] → END
```

**Node Registration:**
```python
workflow.add_node("indexer", index_video_node)
workflow.add_node("auditor", audio_content_node)
workflow.set_entry_point("indexer")
workflow.add_edge("indexer", "auditor")
workflow.add_edge("auditor", END)
```

**Compilation:**
- Compiles to a runnable graph object
- Supports deterministic execution
- Enables state tracing for debugging

#### **nodes.py** - Workflow Step Implementations

##### **Node 1: index_video_node (Indexer)**
**Responsibility**: Download, process, and extract video insights

**Execution Steps:**
1. **Video Download**
   - Validates YouTube URL format
   - Downloads using yt-dlp library
   - Stores locally as temporary file
   
2. **Video Upload**
   - Exchanges Azure tokens (ARM → VI account token)
   - Uploads to Azure Video Indexer
   - Sets privacy to "Private" and indexing preset to "Default"
   
3. **Processing Poll**
   - Polls Video Indexer API every 30 seconds
   - Waits for state: "Processed"
   - Handles failure states: "Failed", "Quarantined"
   
4. **Data Extraction**
   - Extracts transcript from speech-to-text insights
   - Extracts OCR text from video frames
   - Compiles video metadata (duration, platform)

**Error Handling:**
- Returns error dict if any step fails
- Logs detailed error messages
- Populates error list in state

**Return Value:**
```python
{
    "transcript": str,              # Combined speech-to-text
    "ocr_text": List[str],         # Frame text extractions
    "video_metadata": {
        "duration": int,            # Video length in seconds
        "platform": "youtube"
    }
}
```

##### **Node 2: audio_content_node (Auditor)**
**Responsibility**: Analyze content against compliance rules using RAG

**Execution Steps:**
1. **Validation**
   - Checks if transcript exists
   - Returns FAIL if extraction failed
   
2. **AI Model Setup**
   - Initializes Azure OpenAI (GPT-4)
   - Initializes embedding model (text-embedding-3-small)
   - Connects to Azure Search vector database
   
3. **Knowledge Retrieval (RAG)**
   - Combines transcript + OCR text as query
   - Performs semantic similarity search in Azure Search
   - Retrieves top-3 relevant compliance rules
   
4. **LLM Compliance Analysis**
   - Constructs system prompt with regulatory rules
   - Sends video content as human message
   - Requests JSON-formatted compliance analysis
   
5. **Response Parsing**
   - Extracts JSON from potential markdown wrappers
   - Parses compliance_results, status, final_report
   
6. **Error Recovery**
   - Returns FAIL status if JSON parsing fails
   - Logs raw LLM response for debugging

**Prompt Template:**
```
System: "You are a senior brand compliance auditor.
         OFFICIAL REGULATORY RULES: [Retrieved from knowledge base]
         INSTRUCTION: [Analysis instructions]"

User: "VIDEO_METADATA: {...}
       TRANSCRIPT: {...}
       OCR_TEXT: [...]{}"
```

**Return Value:**
```python
{
    "compliance_results": [
        {
            "category": str,         # Type of violation
            "severity": str,         # CRITICAL/HIGH/MEDIUM/LOW
            "description": str       # Detailed finding
        }
    ],
    "final_status": str,            # PASS/FAIL
    "final_report": str             # Executive summary
}
```

---

### 4.3 Service Layer (`backend/src/services/`)

#### **video_indexer.py** - Azure Video Indexer Integration
**Purpose**: Wrapper around Azure Video Indexer API

**Key Methods:**

1. **get_access_token()**
   - Uses Azure Identity DefaultAzureCredential
   - Obtains ARM (Azure Resource Management) token
   - Scope: `https://management.azure.com/.default`

2. **get_account_token(arm_access_token)**
   - Exchanges ARM token for Video Indexer account token
   - API: `/generateAccessToken`
   - Permission: Contributor scope at Account level

3. **download_youtube_video(url, output_path)**
   - Uses yt-dlp for robust YouTube downloading
   - Config: Best format selection
   - Handles age-restricted content with client spoofing
   - Returns: Local file path

4. **upload_video(video_path, video_name)**
   - Multipart form upload to Video Indexer
   - Parameters:
     - `name`: Video identifier
     - `privacy`: Private (not searchable)
     - `indexingPreset`: Default (standard analysis)
   - Returns: Video ID for tracking

5. **wait_for_processing(video_id)**
   - Polling mechanism with 30-second intervals
   - Status states: Processed, Failed, Quarantined, Processing
   - Raises exception on failure
   - Returns: Full JSON insight data when complete

6. **extract_data(vi_json)**
   - Parses Azure VI JSON response
   - Aggregates transcript lines
   - Aggregates OCR text extractions
   - Returns structured data for state

**Azure Video Indexer Capabilities:**
- Automatic speech recognition (multi-language)
- Optical character recognition (OCR)
- Face detection and recognition
- Scene detection
- Branded content detection
- Audio transcription and translation

---

## 5. DATA FLOW & PROCESSING PIPELINE

```
INPUT: YouTube URL
   │
   ▼
┌──────────────────────────────────────┐
│ API Endpoint (/audit)                │
│ - Generate Session ID                │
│ - Create Initial State               │
└──────────────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ INDEXER NODE                 │
        ├──────────────────────────────┤
        │ 1. Download Video (yt-dlp)   │
        │    ├─ Validate URL           │
        │    ├─ Stream to local file   │
        │    └─ Verify download        │
        │                              │
        │ 2. Upload to Azure VI        │
        │    ├─ Get ARM token          │
        │    ├─ Get VI account token   │
        │    ├─ Upload file (multipart)│
        │    └─ Receive Video ID       │
        │                              │
        │ 3. Poll Processing           │
        │    ├─ Every 30s check status │
        │    ├─ Handle failures        │
        │    └─ Wait for "Processed"   │
        │                              │
        │ 4. Extract Insights          │
        │    ├─ Parse transcript JSON  │
        │    ├─ Parse OCR JSON         │
        │    └─ Extract metadata       │
        └──────────────┬───────────────┘
                       │
    ┌──────────────────┴──────────────────┐
    │                                     │
    ▼                                     ▼
TRANSCRIPT                          OCR_TEXT
"Hello, our product features..."   ["Best Choice", "Premium Quality"]
VIDEO_METADATA
{duration: 120, platform: "youtube"}
    │                                     │
    └──────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ AUDITOR NODE                 │
        ├──────────────────────────────┤
        │ 1. Query Knowledge Base      │
        │    ├─ Embed content (text-3) │
        │    ├─ Semantic search        │
        │    └─ Retrieve top-3 rules   │
        │                              │
        │ 2. Invoke GPT-4              │
        │    ├─ Construct prompt       │
        │    ├─ Add compliance rules   │
        │    ├─ Send transcript + OCR  │
        │    └─ Receive JSON response  │
        │                              │
        │ 3. Parse & Validate          │
        │    ├─ Extract JSON           │
        │    ├─ Parse violations       │
        │    └─ Format severity/cat.   │
        │                              │
        │ 4. Generate Report           │
        │    ├─ Summarize findings     │
        │    ├─ Set final status       │
        │    └─ Build response         │
        └──────────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │ COMPLIANCE RESULTS   │
            ├──────────────────────┤
            │ [Violation 1]        │
            │ {                    │
            │   category: "Claim"  │
            │   severity: "HIGH"   │
            │   description: "..." │
            │ }                    │
            │ [Violation 2]        │
            │ ...                  │
            └──────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ AUDIT RESPONSE               │
        ├──────────────────────────────┤
        │ session_id: "uuid"           │
        │ video_id: "vid_uuid"         │
        │ status: "FAIL"               │
        │ final_report: "Summary..."   │
        │ compliance_issues: [...]     │
        └──────────────────────────────┘
                       │
                       ▼
                   OUTPUT
```

---

## 6. TECHNOLOGY STACK & INTEGRATION POINTS

### 6.1 Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Workflow Engine** | LangGraph v1.1.10 | DAG orchestration & state management |
| **LLM Provider** | Azure OpenAI (GPT-4o) | Compliance analysis & understanding |
| **Embeddings** | text-embedding-3-small | Semantic search for compliance rules |
| **Vector Database** | Azure Search v12.0.0 | Store and retrieve compliance rules |
| **Video Processing** | Azure Video Indexer | Extract transcript & OCR from videos |
| **API Framework** | FastAPI v0.136.1 | REST API server |
| **Video Download** | yt-dlp v2026.3.17 | YouTube video downloading |
| **Authentication** | Azure Identity v1.25.3 | Credential management |
| **Data Processing** | Pandas v3.0.2 | Data manipulation |
| **Pydantic v2.13.3** | Data validation | Request/response models |

### 6.2 Azure Services Integration

```
┌─────────────────────────────────────────────────────────────┐
│                  AZURE SUBSCRIPTION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Video Indexer (eastus)                             │   │
│  │ Account ID: 42a678a5-15d0-4859-928a-d10543ec8eac │   │
│  │ ├─ Video Upload & Processing                      │   │
│  │ ├─ Transcript Generation (Speech-to-Text)        │   │
│  │ ├─ OCR Extraction                                │   │
│  │ └─ Metadata Enrichment                           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Azure OpenAI Service (eastus2)                     │   │
│  │ Endpoint: aman-mosaylki-eastus2                   │   │
│  │ ├─ GPT-4o Deployment (Chat)                       │   │
│  │ └─ text-embedding-3-small Deployment              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Azure Search                                       │   │
│  │ Index: azure-com-project                          │   │
│  │ ├─ Compliance Rules Vector Store                  │   │
│  │ ├─ Semantic Search Capability                     │   │
│  │ └─ RAG Knowledge Base                             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Azure Storage (Blob)                              │   │
│  │ Account: ytbrandproject                           │   │
│  │ ├─ Video Storage                                  │   │
│  │ ├─ Audit Reports                                 │   │
│  │ └─ Compliance Logs                               │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Application Insights                              │   │
│  │ ├─ Request Tracing                                │   │
│  │ ├─ Exception Logging                              │   │
│  │ ├─ Performance Metrics                            │   │
│  │ └─ Custom Events                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Resource Group                                    │   │
│  │ azure-compliance-orcestration                     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Third-Party Integrations

| Service | Purpose | Integration |
|---------|---------|-------------|
| **LangSmith** | LLM Tracing & Observability | Environment: LANGCHAIN_API_KEY, LANGCHAIN_PROJECT |
| **LangChain** | LLM Framework & RAG | Orchestrates AI operations |
| **LangChain Community** | Vector Store Integrations | Azure Search connector |
| **LangChain OpenAI** | Azure OpenAI Wrapper | Chat & Embeddings |

---

## 7. EXECUTION MODES

### 7.1 CLI Simulation Mode (`main.py`)
**Purpose**: Local testing and demonstration

```bash
python main.py
```

**Execution Flow:**
1. Generates unique session ID
2. Creates initial state with sample YouTube URL
3. Invokes workflow directly
4. Prints formatted compliance audit report
5. Displays violations in tabular format

**Output Example:**
```
-------------Initializing workflow ------------- 
Input Payload: {
  "video_url": "https://youtu.be/dT7S75eYhcQ",
  "video_id": "vid_<session-id>",
  "compliance_result": [],
  "errors": []
}

Compliance Audit Report--
Video ID: vid_<session-id>
Status: FAIL

[Violation Detected]
- [HIGH] [Claim Validation] [Product claim not substantiated]
- [CRITICAL] [Brand Voice] [Messaging inconsistent with guidelines]

[Final Summary]
2 violations detected. Video requires revision before publishing.
```

### 7.2 API Server Mode
**Purpose**: Production REST API deployment

```bash
uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
```

**OpenAPI Documentation**: `http://localhost:8000/docs`

**Example Request:**
```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtu.be/dT7S75eYhcQ"}'
```

**Example Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": "vid_550e8400-e29b-41d4-a716-446655440000",
  "status": "FAIL",
  "final_report": "Video contains 2 compliance violations...",
  "compliance_issues": [
    {
      "category": "Claim Validation",
      "description": "Product effectiveness claim not substantiated",
      "severity": "HIGH"
    }
  ]
}
```

---

## 8. DEPLOYMENT & CONFIGURATION

### 8.1 Environment Setup

**Required Environment Variables** (.env file):
```
# Azure Services
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Azure Search
AZURE_SEARCH_ENDPOINT=...
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=...

# Azure Video Indexer
AZURE_VI_NAME=...
AZURE_VI_LOCATION=eastus
AZURE_VI_ACCOUNT_ID=...

# Azure Subscription
AZURE_SUBSCRIPTION_ID=...
AZURE_RESOURCE_GROUP=...

# Observability
APPLICATIONINSIGHT_CONNECTION_STRING=...

# LangChain Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=...
```

### 8.2 Dependencies
```toml
[project]
name = "azure-comp-orestration"
version = "0.1.0"
requires-python = ">=3.13"

dependencies = [
    "azure-identity>=1.25.3",
    "azure-monitor-opentelemetry>=1.8.7",
    "azure-search-documents>=12.0.0",
    "azure-storage-blob>=12.28.0",
    "fastapi>=0.136.1",
    "firecrawl-py>=4.24.0",
    "langchain>=1.2.17",
    "langchain-community>=0.4.1",
    "langchain-openai>=1.2.1",
    "langgraph>=1.1.10",
    "langsmith>=0.8.0",
    "opentelemetry-instrumentation-fastapi>=0.61b0",
    "pandas>=3.0.2",
    "psycopg2-binary>=2.9.12",
    "pydantic>=2.13.3",
    "pypdf>=6.10.2",
    "python-dotenv>=1.2.2",
    "redis>=7.4.0",
    "requests>=2.33.1",
    "sqlalchemy>=2.0.49",
    "streamlit>=1.57.0",
    "uvicorn>=0.46.0",
    "yt-dlp>=2026.3.17",
]
```

---

## 9. KEY FEATURES & CAPABILITIES

### 9.1 Functional Features
✅ **Automated Video Processing** - Download, process, and analyze YouTube videos  
✅ **Multi-Modal Analysis** - Combines speech, text, OCR, and metadata  
✅ **RAG-Enhanced Compliance** - Semantic search of compliance rules via vector DB  
✅ **AI-Powered Detection** - GPT-4 intelligent violation identification  
✅ **Severity Classification** - Categorizes issues by CRITICAL/HIGH/MEDIUM/LOW  
✅ **Executive Reports** - Generates comprehensive audit summaries  
✅ **RESTful API** - Production-ready FastAPI endpoints  
✅ **Health Monitoring** - Built-in health check endpoint  

### 9.2 Non-Functional Features
✅ **Scalability** - Async processing pipeline; concurrent audit support  
✅ **Reliability** - Comprehensive error handling at each node  
✅ **Observability** - Application Insights + LangSmith tracing  
✅ **Security** - Azure Identity authentication; secure token management  
✅ **Maintainability** - Modular service architecture; separation of concerns  
✅ **Logging** - Structured logging with timestamps and severity levels  
✅ **Extensibility** - Easy to add new compliance rules via Azure Search  

---

## 10. WORKFLOW EXECUTION EXAMPLE

```
INPUT: Audit request for "https://youtu.be/dT7S75eYhcQ"

STEP 1: API Receives Request
├─ Generates session_id: "abc123..."
├─ Generates video_id: "vid_abc123..."
└─ Initializes state with empty compliance_results

STEP 2: Indexer Node Executes
├─ Downloads video to temp file (~2-5 min depending on video length)
├─ Uploads to Azure Video Indexer (~1-10 min)
├─ Polls processing status every 30 seconds
├─ Extracts:
│  ├─ Transcript: "Welcome to our product demo. Our solution provides..."
│  ├─ OCR: ["Product Name", "99.9% Uptime SLA", "Enterprise Ready"]
│  └─ Metadata: {duration: 180 seconds, platform: youtube}
└─ State updated with extracted data

STEP 3: Auditor Node Executes
├─ Combines transcript + OCR into query
├─ Embeds query using text-embedding-3-small
├─ Searches Azure Search for top-3 compliance rules:
│  ├─ Rule 1: "All product claims must be backed by clinical trials"
│  ├─ Rule 2: "SLA claims must include terms & conditions reference"
│  └─ Rule 3: "Enterprise feature claims require usage documentation"
├─ Constructs GPT-4 prompt with:
│  ├─ System: Compliance auditor role + retrieved rules
│  └─ User: Video content (transcript + OCR + metadata)
├─ Invokes GPT-4o, receives JSON:
│  {
│    "compliance_results": [
│      {
│        "category": "Claim Validation",
│        "severity": "HIGH",
│        "description": "99.9% SLA claim lacks terms reference"
│      }
│    ],
│    "status": "FAIL",
│    "final_report": "1 violation found. Video requires revision."
│  }
├─ Parses and validates response
└─ State updated with compliance results

STEP 4: Return Final State
└─ AuditResponse returned:
   {
     "session_id": "abc123...",
     "video_id": "vid_abc123...",
     "status": "FAIL",
     "final_report": "1 violation found. Video requires revision.",
     "compliance_issues": [
       {
         "category": "Claim Validation",
         "severity": "HIGH",
         "description": "99.9% SLA claim lacks terms reference"
       }
     ]
   }

TOTAL EXECUTION TIME: ~10-20 minutes (mostly Azure VI processing time)
```

---

## 11. ERROR HANDLING & RESILIENCE

### 11.1 Error Scenarios

| Scenario | Handling |
|----------|----------|
| **Invalid YouTube URL** | Validation in Indexer; returns error in state |
| **Video Download Failure** | yt-dlp retry logic + detailed error logging |
| **Video Upload Failure** | Returns error with HTTP status |
| **Video Processing Failure** | Detects "Failed" state; raises exception |
| **Transcript Extraction Failure** | Auditor skips analysis; returns FAIL status |
| **LLM JSON Parse Error** | Catches parse exception; returns FAIL status |
| **Azure Service Outage** | Propagates error; returns 500 HTTP status |
| **Authentication Failure** | Azure Identity retry; raises credential exception |

### 11.2 Logging Strategy
```
INFO:  Workflow start/end, node transitions, major milestones
DEBUG: Detailed API calls, state transitions, data transformations
ERROR: Exception details, failed operations, retry attempts
```

---

## 12. PERFORMANCE CONSIDERATIONS

### 12.1 Processing Timeline
| Phase | Duration | Notes |
|-------|----------|-------|
| Video Download | 2-5 min | Depends on video length and network |
| Video Upload | 1-2 min | Azure infrastructure upload |
| Video Processing | 3-10 min | Azure VI AI analysis time |
| Compliance Analysis | 30-60 sec | GPT-4 inference time |
| **Total** | **~8-18 min** | Mostly async operations |

### 12.2 Optimization Opportunities
- Cache processed videos for re-audit
- Implement batch processing for multiple videos
- Use Azure AI Search pre-computed embeddings
- Implement request queuing for high concurrency

---

## 13. MONITORING & OBSERVABILITY

### 13.1 Metrics Tracked
- **API Latency**: Time from request to response
- **Processing Success Rate**: % of audits completed successfully
- **Compliance Violation Rates**: Distribution of violation types
- **Error Types**: Categorization of failures
- **Azure Service Usage**: Video Indexer, OpenAI, Search API calls

### 13.2 Logging Points
- API request/response
- Workflow state transitions
- Video download/upload
- Azure service API calls
- LLM prompts and responses
- Error stack traces
- Performance metrics

### 13.3 Trace Chains
LangSmith captures:
- Complete LLM call chain
- Token usage (input/output)
- Latency per operation
- Semantic search results
- Compliance decision reasoning

---

## 14. FUTURE ENHANCEMENTS

### Phase 2 Roadmap
- [ ] Web UI for compliance report visualization
- [ ] Compliance rule management dashboard
- [ ] Multi-video batch processing
- [ ] Real-time audit websocket updates
- [ ] Compliance trends analysis
- [ ] False positive feedback loop
- [ ] Webhook notifications
- [ ] Database persistence of audit history
- [ ] Custom compliance rule sets per organization
- [ ] Support for non-YouTube video sources
- [ ] Multi-language support
- [ ] Compliance metrics dashboard

---

## 15. SECURITY & COMPLIANCE

### 15.1 Security Measures
- Azure Identity for secure authentication
- Environment variables for secrets (not hardcoded)
- Private video settings in Azure VI
- Network isolation via Azure VNets (optional)
- HTTPS for all API communications
- Input validation on all endpoints

### 15.2 Data Privacy
- Temporary files deleted after processing
- Videos marked private in Azure VI
- No persistent local storage
- Audit logs retention per compliance needs

---

## 16. CONCLUSION

The Azure Compliance Orchestration system represents a **production-ready, scalable solution** for automating video compliance audits. By combining Azure's powerful AI services (Video Indexer, OpenAI, Search) with intelligent workflow orchestration (LangGraph), it delivers:

✅ Automated compliance checking at scale  
✅ Intelligent violation detection using GPT-4  
✅ Knowledge-driven analysis via semantic search  
✅ Production-grade monitoring and observability  
✅ Extensible architecture for future enhancements  

The system is ready for deployment in enterprise environments where consistent, automated video compliance auditing is critical.

---

**Project Version**: 0.1.0  
**Last Updated**: May 15, 2026  
**Status**: Development Ready
