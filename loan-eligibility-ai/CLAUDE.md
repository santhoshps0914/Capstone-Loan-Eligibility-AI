# CLAUDE.md - Project Guide

This document provides instructions for working with the Loan Eligibility AI application.

## Project Overview

**Loan Eligibility AI** is a full-stack application that assesses loan eligibility using multi-agent AI architecture. The system combines:
- **Streamlit Frontend** (Port 8501): Interactive web UI for loan applications
- **FastAPI Backend** (Port 8000): REST API for processing requests
- **Multi-Agent System**: Coordinator, eligibility, and RAG agents
- **PDF Generation**: Professional reports with color-coded assessments

## Code Organization

```
agents/              # Core business logic
  ├── api.py        # FastAPI server (Uvicorn on :8000)
  ├── coordinator.py  # Main orchestrator agent
  ├── eligibility_agent.py  # Credit scoring & rules
  ├── rag_stub.py   # Evidence retrieval (stub)
  └── rag_adapters.py  # FAISS/Pinecone integration

schemas/             # Pydantic models
  └── models.py     # Request/response validation

ui/                  # Frontend
  └── app.py        # Streamlit application

tests/               # Unit tests
  └── test_eligibility.py

examples/            # Demonstrations
  └── run_embeddings_demo.py
```

## How to Work on This Project

### Running Services

**Always run both services for full functionality:**

```bash
# Terminal 1: Backend
source .venv/bin/activate
python -m uvicorn agents.api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
source .venv/bin/activate
streamlit run ui/app.py
```

**Access:**
- UI: http://localhost:8501
- API: http://localhost:8000/docs

### Making Changes

#### Frontend Changes (`ui/app.py`)
- Streamlit hot-reloads automatically on file save
- Test by interacting with the form in browser
- Check browser console for JavaScript errors
- Test PDF download functionality after changes

#### Backend Changes (`agents/`)
- FastAPI reloads automatically with `--reload` flag
- Test API with: `curl -X POST http://localhost:8000/process -H "Content-Type: application/json" -d '{"name":"test","age":30,"monthly_income":50000,"existing_emi":5000,"credit_score":700,"employment_type":"salaried","loan_amount_required":500000}'`
- Review OpenAPI docs at http://localhost:8000/docs

#### Adding New Rules
Edit `agents/eligibility_agent.py`:
- Add rule to `EligibilityAgent.assess()` method
- Update reasoning list with clear explanation
- Test with pytest: `pytest tests/test_eligibility.py -v`

### Testing Requirements

Always run tests before committing:
```bash
pytest -v                          # Verbose output
pytest tests/test_eligibility.py   # Eligibility tests only
```

Tests validate:
- Credit scoring logic
- EMI ratio calculations
- Age eligibility rules
- Employment type checks
- Reasoning generation

### Common Tasks

#### Task: Change Eligibility Rules
1. Edit `agents/eligibility_agent.py` → `assess()` method
2. Update thresholds or add new rules
3. Add reasoning explanation
4. Run tests: `pytest tests/test_eligibility.py -v`
5. Test in Streamlit UI with edge cases

**Example:**
```python
# In eligibility_agent.py
if credit_score < 650:  # Changed from 700
    reasoning.append(f"Credit score ({credit_score}) is below 650")
    meets_all = False
```

#### Task: Add New Input Field
1. Edit `schemas/models.py` → add field to `LoanApplicationRequest`
2. Update `ui/app.py` → add `st.number_input()` or `st.selectbox()`
3. Update `agents/eligibility_agent.py` → use field in assessment
4. Add test case in `tests/test_eligibility.py`

#### Task: Change PDF Layout
1. Edit `ui/app.py` → `generate_pdf()` function
2. Use ReportLab Canvas API (not Platypus tables)
3. Test by clicking "Evaluate" and downloading PDF
4. Check layout with various credit score ranges

#### Task: Add New API Endpoint
1. Add route in `agents/api.py`:
```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```
2. Test with curl
3. Update README.md with endpoint docs

#### Task: Update RAG/Evidence
1. Edit `agents/rag_stub.py` → modify return data
2. Or integrate real retriever from `agents/rag_adapters.py`
3. Update tests for new evidence format
4. Verify evidence displays in PDF and UI

## Key Design Decisions

### Why Canvas API for PDF (Not Platypus)
- Platypus table styling has alignment bugs in newer ReportLab
- Canvas API gives direct control, avoids table complexities
- Simpler, more reliable for our use case

### Why FastAPI + Streamlit (Not Single Service)
- FastAPI handles backend logic reusably (testable, scalable)
- Streamlit focuses on UI/UX with auto-reload
- Easy to swap frontend later (React, Vue, etc.)
- Enables concurrent requests without Streamlit constraints

### Why Pydantic Models
- Built-in validation at API boundary
- Clear schema documentation
- Type hints for IDE support

### Why Multi-Agent Architecture
- Coordinator orchestrates decision flow
- EligibilityAgent encapsulates business logic
- RAG agent provides evidence independently
- Easy to extend or swap individual agents

## Important Notes

### Color Coding
- **Green (#28a745):** Credit score ≥ 700 OR "Eligible" decision
- **Yellow (#ffc107):** Credit score < 700 OR "Needs Manual Review"
- **Red (#dc3545):** "Not Eligible" decision

Keep colors consistent across:
- PDF reports (`generate_pdf()`)
- Streamlit UI (`st.success()`, `st.warning()`, `st.error()`)

### Port Management
- Streamlit: Port 8501 (auto-assigned if busy)
- FastAPI: Port 8000 (must be available)
- If ports conflict:
  ```bash
  lsof -i :8000  # Check what's using port 8000
  kill -9 <PID>  # Kill process
  ```

### Error Handling
- API errors return JSON with detail message
- Streamlit shows user-friendly errors with `st.error()`
- PDF generation fails gracefully with error message
- Always test error paths (bad input, API down, etc.)

### Performance Considerations
- API response time target: <200ms
- PDF generation: <1s per report
- Keep credit scoring calculations simple
- Avoid blocking operations in Streamlit

## Debugging

### Streamlit Issues
```bash
# Clear cache and restart
streamlit cache clear
streamlit run ui/app.py

# Check logs
tail -f ~/.streamlit/logs/2024-*.log
```

### FastAPI Issues
```bash
# Check API is responding
curl http://localhost:8000/docs

# Check for errors in terminal where API is running
# Look for traceback output
```

### PDF Generation Issues
```bash
# Test PDF generation directly in Python
python -c "
from ui.app import generate_pdf
data = {'name': 'Test', 'age': 30, ...}
response = {'decision': 'Eligible', ...}
pdf = generate_pdf(data, response, 750)
print('PDF size:', len(pdf.getvalue()))
"
```

## Before Committing

Checklist for any changes:
- [ ] Code follows existing patterns and style
- [ ] All tests pass: `pytest -v`
- [ ] Tested in Streamlit UI (if frontend change)
- [ ] Tested API endpoint (if backend change)
- [ ] No hardcoded values (use configs/env vars)
- [ ] Error handling is appropriate
- [ ] README.md updated if needed
- [ ] CLAUDE.md updated if adding new patterns

## File Dependencies

**Important relationships:**
- `schemas/models.py` ← used by `agents/api.py` and `agents/coordinator.py`
- `agents/api.py` ← calls `agents/coordinator.py`
- `agents/coordinator.py` ← uses `agents/eligibility_agent.py` and `agents/rag_stub.py`
- `ui/app.py` ← calls `agents/api.py` via HTTP
- `tests/test_eligibility.py` ← tests `agents/eligibility_agent.py`

**When changing a core module:**
1. Update the module itself
2. Check all files that import it
3. Run all tests
4. Test both API and UI endpoints

## Deployment Notes

### Local Development
```bash
source .venv/bin/activate
python -m uvicorn agents.api:app --host 0.0.0.0 --port 8000 --reload
streamlit run ui/app.py
```

### Production Deployment
- Use proper ASGI server (Gunicorn + Uvicorn)
- Enable HTTPS/TLS
- Add authentication layer
- Use environment variables for secrets
- Enable logging and monitoring
- Consider containerization (Docker)

### Environment Variables
```bash
# Optional - defaults shown
STREAMLIT_SERVER_PORT=8501
FASTAPI_PORT=8000
FASTAPI_HOST=0.0.0.0
```

## Future Work Guidelines

When adding new features:
1. Discuss architecture changes first (separate branch/PR)
2. Keep agents isolated and testable
3. Add schema validation for new inputs
4. Update tests alongside code
5. Document in README and CLAUDE.md
6. Consider backward compatibility

### Potential Extensions
- Database persistence (PostgreSQL)
- User authentication (JWT)
- Admin dashboard
- Webhook notifications
- Real-time status updates (WebSocket)
- Mobile app companion

## Questions?

If something is unclear:
1. Check README.md for overview
2. Review code comments in relevant file
3. Check existing tests for usage examples
4. Search for TODOs in codebase: `grep -r "TODO" --include="*.py"`

---

**Last Updated:** August 2026
**Version:** 1.0.0
