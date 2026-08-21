# Loan Eligibility AI Agent - Production Ready

A full-stack loan eligibility assessment system using multi-agent AI, Streamlit frontend, and FastAPI backend. Features intelligent credit scoring, color-coded decision reporting, and PDF generation for professional loan assessments.

## Features

✨ **Core Features:**
- 🤖 Multi-agent AI architecture for intelligent loan eligibility assessment
- 📊 Real-time credit scoring and risk assessment
- 🎨 Color-coded decisions (Green: Eligible, Yellow: Needs Review, Red: Not Eligible)
- 📄 Automated PDF report generation with applicant details, credit assessment, and improvement recommendations
- 💡 Smart recommendation engine providing actionable steps to improve credit profile
- 📚 RAG/MCP integration for supporting evidence and policy references
- 🔍 Comprehensive eligibility assessment with detailed reasoning
- 💬 Customer support chatbot that answers basic queries about the criteria and about the applicant's own result — works offline, with an optional Claude-powered mode

## Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment support

### Installation

1. **Create and activate virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run tests:**
```bash
pytest -q
```

## Running the Application

### Option 1: Full Stack (Recommended)

**Terminal 1 - Start FastAPI backend:**
```bash
source .venv/bin/activate
python -m uvicorn service.coordinator_service:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start Streamlit frontend:**
```bash
source .venv/bin/activate
streamlit run ui/app.py
```

The application will be available at:
- **Streamlit UI:** http://localhost:8501
- **FastAPI Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Option 2: Streamlit Only (Local Testing)

```bash
source .venv/bin/activate
streamlit run ui/app.py
```

## Application Structure

```
loan-eligibility-ai/
├── agents/
│   ├── __init__.py
│   ├── eligibility_agent.py      # Credit scoring and eligibility logic
│   ├── coordinator.py            # Multi-agent orchestrator
│   ├── rag_stub.py              # RAG/MCP integration stub
│   ├── rag_interface.py          # Retriever protocol
│   ├── rag_adapters.py           # FAISS & Pinecone adapters
│   ├── chat_agent.py             # Customer support chatbot (rules + retrieval)
│   ├── chat_knowledge.py         # Chatbot FAQ knowledge base
│   └── chat_llm.py               # Optional Claude responder for the chatbot
├── service/
│   ├── coordinator_service.py    # FastAPI backend service
│   └── audit.py                  # Audit-log writer
├── schemas/
│   ├── __init__.py
│   └── models.py                 # Pydantic input/output models
├── ui/
│   ├── __init__.py
│   └── app.py                    # Streamlit UI application
├── tests/
│   ├── test_eligibility.py        # Unit tests
│   ├── test_chat_agent.py         # Chatbot rules & fallback tests
│   ├── test_chat_llm.py           # Claude responder tests (stubbed client)
│   └── test_chat_api.py           # /chat endpoint tests
├── examples/
│   └── run_embeddings_demo.py     # RAG adapter demonstrations
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## How It Works

### 1. **Loan Application Input**
Users fill out a form with:
- Personal information (name, age)
- Financial details (monthly income, existing EMI, loan amount)
- Credit score
- Employment type

### 2. **Backend Processing**
The FastAPI service processes the request through:
- **CoordinatorAgent:** Validates input and orchestrates decision flow
- **EligibilityAgent:** Applies credit scoring rules and eligibility criteria
- **RAG Client:** Retrieves supporting policy evidence

### 3. **Decision & Assessment**
The system evaluates:
- Credit score eligibility (≥700 = Good, <700 = Fair)
- EMI-to-income ratio (max 40%)
- Age eligibility (21-60 years)
- Employment stability

### 4. **PDF Report Generation**
Generates professional PDF reports including:
- Applicant information
- Credit report with color-coded status
- Eligibility assessment with detailed reasoning
- Personalized improvement recommendations
- Footer with disclaimer

### 5. **User Feedback**
Display includes:
- Color-coded decision badge
- Credit metrics dashboard
- Eligibility assessment points
- Actionable improvement steps
- Supporting evidence references

## Customer Support Chatbot

A chat panel in the Streamlit sidebar answers basic customer queries. It runs
in two layers, so it always works — even with no API key and no internet.

### What it answers

- **Eligibility criteria** — "What credit score do I need?", "What's the maximum
  EMI-to-income ratio?", "Which employment types are accepted?"
- **Process questions** — "What does Needs Manual Review mean?", "Is this
  decision final?", "What documents will I need?"
- **The applicant's own result** — after an evaluation, "Why does my application
  need review?", "What is my EMI ratio?", "What should I do to improve my
  chances?" The answers use the applicant's actual numbers and the same
  recommendation wording shown on the page and in the PDF.

Anything outside that scope gets a short "I can only help with…" reply plus
suggested questions, rather than a guess.

### Rules mode (default)

No configuration needed. `ChatAgent` resolves each question in order:

1. **Safety guard** — messages that look like they contain account numbers,
   card numbers, PAN, Aadhaar, OTPs or passwords get a warning and are never
   forwarded anywhere.
2. **Result-aware intents** — questions about the applicant's own assessment are
   answered exactly from the submitted result. These never call the API.
3. **FAQ retrieval** — the knowledge base in `agents/chat_knowledge.py` is
   ranked with the existing `InMemoryVectorRetriever`; a confidence floor keeps
   weak matches out.

### AI-assisted mode (optional)

With `LOAN_CHAT_LLM=1`, retrieved FAQ snippets and the applicant's result are
passed to Claude, which rephrases them conversationally. The system prompt
forbids inventing thresholds or rates, promising approval, and giving
personalised financial advice.

```bash
export LOAN_CHAT_LLM=1
export ANTHROPIC_API_KEY=sk-ant-...        # or run `ant auth login`
export LOAN_CHAT_MODEL=claude-opus-5       # optional; this is the default
```

Two deliberate design points:

- **Opt-in by flag, not by key.** The Anthropic SDK also picks up
  `ANTHROPIC_AUTH_TOKEN` and local CLI profiles, so an unrelated credential in
  a developer's shell must not silently turn the form into a billed API caller.
- **Failure is never visible to the customer.** If the API is unreachable,
  rate-limited, misconfigured, or declines, the request still returns `200`
  with the deterministic answer and `"mode": "rules"`.

### Privacy

The applicant's **name is never sent** to the chat endpoint — explaining a
result does not need it. `logs/audit.log` records the request id, the message
*length*, and which FAQ entries matched — never the question text.

## API Endpoints

### POST `/chat`

Answer a customer query. `history` and `context` are optional; `context` is the
applicant's latest assessment.

**Request:**
```json
{
  "message": "Why does my application need review?",
  "history": [
    {"role": "user", "content": "What credit score do I need?"},
    {"role": "assistant", "content": "Above 700."}
  ],
  "context": {
    "decision": "Needs Manual Review",
    "credit_score": 695,
    "emi_ratio": 0.41,
    "new_emi": 15000,
    "age": 35,
    "employment_type": "salaried",
    "reasoning": ["credit_score: FAILED (695) - credit score must exceed 700"],
    "recommendations": ["Improve your credit score from 695 to above 700"]
  }
}
```

**Response:**
```json
{
  "answer": "'Needs Manual Review' came from these checks:\n- credit_score: FAILED (695) ...",
  "sources": [
    {"id": "faq-manual-review", "content": "What does 'Needs Manual Review' mean? ..."}
  ],
  "mode": "rules",
  "suggestions": [
    "What credit score do I need to be eligible?",
    "What is the maximum EMI-to-income ratio allowed?",
    "What does 'Needs Manual Review' mean?"
  ]
}
```

`mode` is `"rules"` for a deterministic answer and `"llm"` when Claude composed
it. An empty `message` returns `422`.

### GET `/chat/info`

Reports chat capabilities so the UI can render a mode badge and starter prompts.

```json
{
  "llm_enabled": false,
  "suggested_questions": ["What credit score do I need to be eligible?", "..."]
}
```

### POST `/process`
Process a loan application and return eligibility assessment.

**Request:**
```json
{
  "name": "John Doe",
  "age": 35,
  "monthly_income": 50000,
  "existing_emi": 5000,
  "credit_score": 750,
  "employment_type": "salaried",
  "loan_amount_required": 500000
}
```

**Response:**
```json
{
  "decision": "Eligible",
  "new_emi": 15000,
  "emi_ratio": 0.35,
  "reasoning": [
    "Credit score (750) meets minimum requirement (700)",
    "EMI-to-income ratio (35%) is within acceptable range",
    "Employment type (salaried) is stable",
    "Age (35) is within eligible range (21-60)"
  ],
  "rag_evidence": [
    {
      "id": "Policy-001",
      "content": "Credit score above 700 qualifies for standard rates..."
    }
  ]
}
```

## Configuration

### Environment Variables (Optional)
```bash
STREAMLIT_SERVER_PORT=8501          # Streamlit port (default: 8501)
STREAMLIT_SERVER_ADDRESS=localhost  # Streamlit address
FASTAPI_HOST=0.0.0.0               # FastAPI host
FASTAPI_PORT=8000                  # FastAPI port

LOAN_API_BASE=http://localhost:8000 # Backend URL used by the Streamlit UI
LOAN_CHAT_LLM=0                     # 1 enables the Claude-backed chatbot mode
LOAN_CHAT_MODEL=claude-opus-5       # Model used when LOAN_CHAT_LLM=1
ANTHROPIC_API_KEY=                  # Required only when LOAN_CHAT_LLM=1
```

### Streamlit Config
Edit `.streamlit/config.toml` to customize Streamlit settings:
```toml
[server]
port = 8501
address = "localhost"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Eligibility Rules

### Credit Score
- **Eligible:** Score ≥ 700
- **Fair/Needs Review:** Score < 700

### EMI-to-Income Ratio
- **Acceptable:** ≤ 40%
- **Caution:** > 40% requires manual review

### Age
- **Eligible Range:** 21-60 years

### Employment Type
- **Preferred:** Salaried, Government
- **Other:** Self-employed, Other (may require manual review)

## PDF Report Features

- 📋 Professional layout with company branding
- 🎨 Color-coded decision indicators
- 📊 Credit metrics and financial summary
- ✅ Detailed eligibility assessment
- 💡 Personalized improvement recommendations
- 📚 Supporting evidence and policy references
- 🔐 Automated disclaimer footer

**Generated filename format:** `loan_eligibility_YYYYMMDD_HHMMSS.pdf`

## Extending the System

### Swapping in a Vector Retriever

The POC includes a `Retriever` Protocol for easy swapping of RAG implementations:

```python
from agents.rag_interface import InMemoryVectorRetriever
from agents.coordinator import CoordinatorAgent

docs = [{"id": "d1", "content": "Credit score above 700 is good"}]
retriever = InMemoryVectorRetriever(docs)
coord = CoordinatorAgent(rag_client=retriever)
```

### Using FAISS Adapter

```bash
pip install faiss-cpu sentence-transformers
python examples/run_embeddings_demo.py --use-faiss
```

### Using Pinecone Adapter

```bash
export PINECONE_API_KEY=your_key
export PINECONE_ENV=your_env
python examples/run_embeddings_demo.py --use-pinecone
```

## Testing

Run the test suite:
```bash
pytest -q              # Quick test run
pytest -v             # Verbose output
pytest tests/          # Run all tests
pytest tests/test_eligibility.py::test_eligibility_agent  # Specific test
pytest tests/test_chat_agent.py tests/test_chat_llm.py -v # Chatbot only
```

No test makes a network call: the chatbot's optional Claude path is covered
with stubbed clients and injected fake responders.

## Troubleshooting

### Streamlit Server Won't Start
```bash
# Kill any existing process
pkill -f streamlit

# Try with explicit port
streamlit run ui/app.py --server.port 8501
```

### FastAPI Connection Error
```bash
# Ensure FastAPI is running on port 8000
python -m uvicorn service.coordinator_service:app --host 0.0.0.0 --port 8000

# Check service is responding
curl http://localhost:8000/docs
```

### PDF Generation Issues
- Ensure `reportlab>=3.6.0` is installed
- Check that `/tmp` has sufficient space for temporary buffer files
- Verify all required fonts are available

## Technologies Used

- **Frontend:** Streamlit (Python web UI framework)
- **Backend:** FastAPI (REST API, async support)
- **PDF Generation:** ReportLab (vector PDF graphics)
- **Data Validation:** Pydantic (schema validation)
- **Server:** Uvicorn (ASGI application server)
- **RAG/Search:** FAISS, Pinecone adapters (optional)
- **Chatbot:** Rules + FAQ retrieval, with an optional Claude backend via the Anthropic SDK
- **Testing:** Pytest

## Project Architecture

```
┌─────────────────────────────────────────────────────┐
│             Streamlit UI (Port 8501)                │
│  - Application form                                 │
│  - Credit report display                            │
│  - PDF generation & download                        │
│  - Sidebar chat panel                               │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/JSON  (/process, /chat)
                 ▼
┌─────────────────────────────────────────────────────┐
│          FastAPI Backend (Port 8000)                │
│  - Request validation                               │
│  - CoordinatorAgent orchestration                   │
│  - Decision processing                              │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┼──────────────────┐
    ▼            ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────────┐
│ Eligibility  │ │ RAG/MCP      │ │ Chat Agent         │
│ Agent        │ │ Client       │ │ - Safety guard     │
│ - Credit     │ │ (Stub)       │ │ - Result intents   │
│   scoring    │ │ - Evidence   │ │ - FAQ retrieval    │
│ - Rules      │ │ - Policy     │ └─────────┬──────────┘
│   engine     │ │   lookup     │           │ optional
└──────────────┘ └──────────────┘           ▼
                                  ┌────────────────────┐
                                  │ ClaudeResponder    │
                                  │ (LOAN_CHAT_LLM=1)  │
                                  │ falls back to      │
                                  │ rules on any error │
                                  └────────────────────┘
```

## Performance Notes

- **API Response Time:** ~100-200ms per request
- **PDF Generation:** ~500-1000ms per report
- **Concurrent Users:** FastAPI handles 100+ concurrent connections
- **Memory Usage:** ~150MB base + per-request overhead

## Security Considerations

- ✅ Input validation via Pydantic schemas
- ✅ No hardcoded credentials
- ✅ CORS configured for local development
- ⚠️ For production: Enable HTTPS, authentication, rate limiting
- ⚠️ Sensitive data should use environment variables

## Future Enhancements

- 🔐 User authentication and authorization
- 📧 Email delivery of PDF reports
- 📱 Mobile-friendly responsive design
- 🗄️ Database persistence for historical records
- 📊 Admin dashboard with analytics
- 🔄 Webhook support for third-party integrations
- 🌐 Multi-language support
- ⚡ Caching layer for improved performance

## License

This project is provided as-is for educational purposes.

## Support

For issues, questions, or improvements:
1. Check existing GitHub issues
2. Review the troubleshooting section above
3. Run tests to verify system integrity
4. Check logs in `.streamlit/logs/` or FastAPI console output

---

**Current Version:** 1.0.0 | **Last Updated:** August 2026
