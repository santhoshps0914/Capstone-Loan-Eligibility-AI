"""Modern Interactive Streamlit UI for Loan Eligibility AI

Run with: `streamlit run ui/app.py`
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from agents.coordinator import CoordinatorAgent
import html
import os
import requests
import uuid
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdfcanvas
import time


# Backend location — override with LOAN_API_BASE when the service is not local.
API_BASE = os.getenv("LOAN_API_BASE", "http://localhost:8000")


def generate_pdf(data, response, credit_score):
    """Generate a professional PDF report using canvas."""
    buffer = BytesIO()
    c = pdfcanvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    c.setFont("Helvetica-Bold", 20)
    title = "LOAN ELIGIBILITY ASSESSMENT REPORT"
    c.drawCentredString(width/2, y, title)
    y -= 30

    c.line(30, y, width-30, y)
    y -= 15

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 15
    c.drawString(40, y, f"Applicant: {data.get('name', 'N/A')}")
    y -= 15
    c.drawString(40, y, f"Report ID: {str(uuid.uuid4())[:8]}")
    y -= 25

    decision = response.get("decision", "N/A")
    c.setFont("Helvetica-Bold", 14)

    if decision == "Eligible":
        c.setFillColor(colors.HexColor('#28a745'))
    elif decision == "Needs Manual Review":
        c.setFillColor(colors.HexColor('#ffc107'))
    else:
        c.setFillColor(colors.HexColor('#dc3545'))

    decision_text = f"DECISION: {decision}"
    c.drawCentredString(width/2, y, decision_text)
    c.setFillColor(colors.black)
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "APPLICANT INFORMATION")
    y -= 15

    c.setFont("Helvetica", 10)
    app_info = [
        f"Age: {data.get('age', 'N/A')}",
        f"Monthly Income: ₹ {data.get('monthly_income', 0):,.2f}",
        f"Existing EMI: ₹ {data.get('existing_emi', 0):,.2f}",
        f"Loan Amount Required: ₹ {data.get('loan_amount_required', 0):,.2f}",
        f"Employment Type: {data.get('employment_type', 'N/A').title()}"
    ]
    for info in app_info:
        c.drawString(60, y, info)
        y -= 12
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "CREDIT REPORT")
    y -= 15

    c.setFont("Helvetica", 10)
    credit_info = [
        f"Credit Score: {credit_score}/1000",
        f"Status: {'✓ Good' if credit_score >= 700 else '⚠ Fair - Needs Improvement'}",
        f"Estimated New EMI: ₹ {response.get('new_emi', 0):,.2f}",
        f"EMI-to-Income Ratio: {response.get('emi_ratio', 0):.2%}"
    ]
    for info in credit_info:
        c.drawString(60, y, info)
        y -= 12
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "ELIGIBILITY ASSESSMENT")
    y -= 15

    c.setFont("Helvetica", 9)
    for line in response.get("reasoning", []):
        wrapped_text = wrap_text(line, 85)
        for text_line in wrapped_text:
            c.drawString(60, y, f"• {text_line}")
            y -= 10
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "RECOMMENDATIONS FOR IMPROVEMENT")
    y -= 15

    recommendations = get_recommendations(response, credit_score, data)
    c.setFont("Helvetica", 9)

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            wrapped_text = wrap_text(rec, 85)
            for j, text_line in enumerate(wrapped_text):
                if j == 0:
                    c.drawString(60, y, f"{i}. {text_line}")
                else:
                    c.drawString(70, y, text_line)
                y -= 10
    else:
        c.drawString(60, y, "No improvements needed. You are eligible for the loan!")
        y -= 10

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 20, "This is an automated assessment and subject to manual review.")

    c.save()
    buffer.seek(0)
    return buffer


def wrap_text(text, max_length):
    """Wrap text to fit within max_length characters."""
    if len(text) <= max_length:
        return [text]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += (" " + word) if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def get_recommendations(response, credit_score, data):
    """Generate recommendations based on assessment results."""
    recommendations = []

    if credit_score < 700:
        recommendations.append(f"Improve your credit score from {credit_score} to above 700 by maintaining timely payments")
        recommendations.append("Check your credit report for errors and dispute any inaccuracies")
        recommendations.append("Reduce your credit card utilization below 30%")
        recommendations.append("Avoid opening new credit accounts in the near term")

    emi_ratio = response.get("emi_ratio", 0)
    if emi_ratio > 0.40:
        recommendations.append(f"Your EMI-to-income ratio is {emi_ratio:.2%}. Try to reduce it below 40% by increasing income or reducing other EMIs")

    age = data.get("age", 0)
    if age < 21 or age > 60:
        recommendations.append(f"Your age ({age}) is outside the eligible range (21-60)")

    employment = data.get("employment_type", "")
    if employment not in ["salaried", "govt"]:
        recommendations.append(f"Consider transitioning to stable employment. Currently listed as {employment}")

    return recommendations


@st.cache_data(ttl=60, show_spinner=False)
def get_chat_info():
    """Ask the backend what the chatbot can do. Degrades quietly if it is down."""
    try:
        resp = requests.get(f"{API_BASE}/chat/info", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return {"llm_enabled": False, "suggested_questions": []}


def ask_chatbot(question, context, history):
    """POST one question to /chat. Returns the response dict, or None on error.

    The error message is stored in session state so the sidebar can show it in
    the same card style the main page uses.
    """
    try:
        resp = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": question,
                "history": history[-6:],
                "context": context,
            },
            timeout=30,  # an LLM-backed answer is slower than /process
            headers={"X-Request-ID": str(uuid.uuid4())},
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        st.session_state.chat_error = "The assistant took too long to reply. Please try again."
    except requests.exceptions.ConnectionError:
        st.session_state.chat_error = (
            "Cannot reach the assistant. Make sure the backend is running on port 8000."
        )
    except requests.RequestException as exc:
        st.session_state.chat_error = f"Assistant error: {exc}"
    return None


def render_chat_panel():
    """Sidebar chat panel for basic customer queries."""
    info = get_chat_info()

    st.markdown("### 💬 Ask the Loan Assistant")
    badge = "AI-assisted answers" if info.get("llm_enabled") else "Instant answers from our policy guide"
    st.caption(badge)

    # Transcript is rendered after this run's message is processed, so a new
    # question and its answer both appear immediately.
    transcript = st.empty()

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            placeholder="e.g. What credit score do I need?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    pending = question.strip() if (submitted and question and question.strip()) else None

    if not st.session_state.chat_history:
        for i, suggestion in enumerate(info.get("suggested_questions", [])):
            if st.button(suggestion, key=f"chat_suggestion_{i}", use_container_width=True):
                pending = suggestion
    elif st.button("🧹 Clear chat", key="chat_clear", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.chat_error = None

    if pending:
        st.session_state.chat_error = None
        with st.spinner("Thinking..."):
            result = ask_chatbot(
                pending,
                st.session_state.last_assessment,
                st.session_state.chat_history,
            )
        st.session_state.chat_history.append({"role": "user", "content": pending})
        if result:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result.get("answer", ""),
                "sources": result.get("sources", []),
            })

    with transcript.container():
        if st.session_state.chat_error:
            st.markdown(
                f"<div class='error-card'><small>{html.escape(st.session_state.chat_error)}</small></div>",
                unsafe_allow_html=True,
            )
        for msg in st.session_state.chat_history:
            # Escaped: the transcript is rendered as HTML for styling.
            body = html.escape(msg["content"]).replace("\n", "<br>")
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='chat-user'><small><b>You</b><br>{body}</small></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='chat-bot'><small><b>🤖 Assistant</b><br>{body}</small></div>",
                    unsafe_allow_html=True,
                )
                for src in msg.get("sources", []):
                    with st.expander(f"📖 {src.get('id', 'reference')}"):
                        st.write(src.get("content", ""))

        if not st.session_state.chat_history and not st.session_state.chat_error:
            st.caption("Ask about eligibility criteria, your result, or what happens next.")


def validate_inputs(name, age, monthly_income, existing_emi, credit_score, loan_amount):
    """Validate all user inputs."""
    errors = []

    if not name or name.strip() == "":
        errors.append("❌ Name is required")
    elif len(name.strip()) < 2:
        errors.append("❌ Name must be at least 2 characters long")

    if age < 18 or age > 120:
        errors.append("❌ Age must be between 18 and 120")

    if monthly_income <= 0:
        errors.append("❌ Monthly Income must be greater than 0")

    if monthly_income > 10000000:
        errors.append("❌ Monthly Income seems unreasonably high")

    if existing_emi < 0:
        errors.append("❌ Existing EMI cannot be negative")

    if existing_emi > monthly_income:
        errors.append("❌ Existing EMI cannot exceed monthly income")

    if credit_score < 0 or credit_score > 1000:
        errors.append("❌ Credit Score must be between 0 and 1000")

    if loan_amount <= 0:
        errors.append("❌ Loan Amount must be greater than 0")

    if loan_amount > 100000000:
        errors.append("❌ Loan Amount seems unreasonably high")

    return errors


# Page configuration
st.set_page_config(
    page_title="Loan Eligibility AI",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Intelligent Loan Eligibility Assessment System"}
)

# Initialize session state for form fields
if 'form_name' not in st.session_state:
    st.session_state.form_name = ""
if 'form_age' not in st.session_state:
    st.session_state.form_age = 21
if 'form_income' not in st.session_state:
    st.session_state.form_income = 0.0
if 'form_emi' not in st.session_state:
    st.session_state.form_emi = 0.0
if 'form_credit' not in st.session_state:
    st.session_state.form_credit = 0
if 'form_employment' not in st.session_state:
    st.session_state.form_employment = ""
if 'form_loan' not in st.session_state:
    st.session_state.form_loan = 0.0

# Chatbot state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_error' not in st.session_state:
    st.session_state.chat_error = None
# Latest assessment, so the assistant can explain the customer's own result
if 'last_assessment' not in st.session_state:
    st.session_state.last_assessment = None

def reset_form():
    """Reset all form fields"""
    st.session_state.form_name = ""
    st.session_state.form_age = 21
    st.session_state.form_income = 0.0
    st.session_state.form_emi = 0.0
    st.session_state.form_credit = 0
    st.session_state.form_employment = ""
    st.session_state.form_loan = 0.0

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .success-card {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    .error-card {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    .chat-user {
        background-color: #e8ebf7;
        padding: 8px 12px;
        border-radius: 8px;
        border-left: 3px solid #667eea;
        margin: 6px 0;
    }
    .chat-bot {
        background-color: #f0f2f6;
        padding: 8px 12px;
        border-radius: 8px;
        border-left: 3px solid #28a745;
        margin: 6px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>🤖 Loan Eligibility AI Assessment</h1>
        <p>Intelligent multi-agent system for instant loan eligibility evaluation</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar info
with st.sidebar:
    st.markdown("### 📋 Application Guide")
    st.markdown("""
    **How it works:**
    1. Enter your personal information
    2. Provide financial details
    3. Click "Evaluate" for instant assessment
    4. Download your professional PDF report

    **Decision Criteria:**
    - 🟢 **Eligible**: Credit score ≥700, EMI ratio ≤40%
    - 🟡 **Manual Review**: Borderline cases
    - 🔴 **Not Eligible**: Fails critical thresholds
    """)

    st.divider()
    st.markdown("### ℹ️ Field Requirements")
    st.markdown("""
    - **Name**: Any valid name
    - **Age**: 18-120 years
    - **Income**: Monthly salary/earnings
    - **EMI**: Existing monthly obligations
    - **Credit Score**: 0-1000 range
    - **Loan Amount**: Requested amount
    """)

    st.divider()
    render_chat_panel()

# Main content
st.markdown("### 📝 Enter Your Information")

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("#### 👤 Personal Details")

    name = st.text_input(
        "Full Name *",
        value=st.session_state.form_name,
        placeholder="Enter your full name",
        help="Your legal name as per identification",
        key="input_name"
    )
    st.session_state.form_name = name

    age = st.number_input(
        "Age *",
        min_value=18,
        max_value=120,
        step=1,
        value=st.session_state.form_age,
        placeholder="Enter your age",
        help="Must be between 18 and 120 years",
        key="input_age"
    )
    st.session_state.form_age = age

    employment_type = st.selectbox(
        "Employment Type *",
        options=["", "salaried", "self-employed", "govt", "other"],
        index=0 if st.session_state.form_employment == "" else (["", "salaried", "self-employed", "govt", "other"].index(st.session_state.form_employment) if st.session_state.form_employment in ["", "salaried", "self-employed", "govt", "other"] else 0),
        help="Select your employment category",
        key="input_employment"
    )
    st.session_state.form_employment = employment_type

with col2:
    st.markdown("#### 💰 Financial Information")

    monthly_income = st.number_input(
        "Monthly Income (₹) *",
        min_value=0.0,
        step=1000.0,
        value=st.session_state.form_income,
        placeholder="Enter your monthly income",
        help="Your regular monthly earnings",
        key="input_income"
    )
    st.session_state.form_income = monthly_income

    existing_emi = st.number_input(
        "Existing EMI (₹) *",
        min_value=0.0,
        step=100.0,
        value=st.session_state.form_emi,
        placeholder="Enter existing EMI obligations",
        help="Total monthly EMI payments",
        key="input_emi"
    )
    st.session_state.form_emi = existing_emi

    credit_score = st.number_input(
        "Credit Score *",
        min_value=0,
        max_value=1000,
        step=1,
        value=st.session_state.form_credit,
        placeholder="Enter your credit score",
        help="Your credit score (0-1000)",
        key="input_credit"
    )
    st.session_state.form_credit = credit_score

st.markdown("#### 💳 Loan Details")

col_loan1, col_loan2 = st.columns([1, 1], gap="medium")

with col_loan1:
    loan_amount_required = st.number_input(
        "Loan Amount Required (₹) *",
        min_value=0.0,
        step=10000.0,
        value=st.session_state.form_loan,
        placeholder="Enter loan amount needed",
        help="The amount you want to borrow",
        key="input_loan"
    )
    st.session_state.form_loan = loan_amount_required

with col_loan2:
    st.empty()

# Validation and submission
st.divider()

# Create two columns for buttons
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])

with btn_col1:
    reset_button = st.button("🔄 Clear Form", use_container_width=True, on_click=reset_form)

with btn_col2:
    evaluate_button = st.button("⚡ Evaluate Eligibility", use_container_width=True, type="primary")

if reset_button:
    st.success("✅ Form cleared!")

if evaluate_button:
    # Validate inputs
    validation_errors = validate_inputs(
        name,
        age,
        monthly_income,
        existing_emi,
        credit_score,
        loan_amount_required
    )

    if validation_errors:
        st.markdown("<div class='error-card'>", unsafe_allow_html=True)
        st.markdown("### ⚠️ Validation Errors")
        for error in validation_errors:
            st.markdown(error)
        st.markdown("</div>", unsafe_allow_html=True)

    elif not employment_type:
        st.markdown("<div class='error-card'>", unsafe_allow_html=True)
        st.markdown("### ⚠️ Please select an employment type")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Prepare data
        data = {
            "name": name.strip(),
            "age": int(age),
            "monthly_income": float(monthly_income),
            "existing_emi": float(existing_emi),
            "credit_score": int(credit_score),
            "employment_type": employment_type,
            "loan_amount_required": float(loan_amount_required),
        }

        # Show processing
        with st.spinner("⏳ Evaluating your application..."):
            time.sleep(0.5)
            try:
                req_id = str(uuid.uuid4())
                headers = {"X-Request-ID": req_id}
                resp = requests.post(
                    f"{API_BASE}/process",
                    json=data,
                    timeout=10,
                    headers=headers
                )
                resp.raise_for_status()
                response = resp.json()

                # Generate PDF
                pdf_buffer = generate_pdf(data, response, credit_score)

                # Hand the result to the chatbot so it can explain this decision.
                # Reuses get_recommendations() so the wording stays identical
                # across the page, the PDF and the assistant. Note: no name —
                # explaining a result never needs the applicant's identity.
                st.session_state.last_assessment = {
                    "decision": response.get("decision"),
                    "credit_score": data["credit_score"],
                    "emi_ratio": response.get("emi_ratio"),
                    "new_emi": response.get("new_emi"),
                    "age": data["age"],
                    "employment_type": data["employment_type"],
                    "reasoning": response.get("reasoning", []),
                    "recommendations": get_recommendations(response, credit_score, data),
                }

                # Display results
                st.divider()
                st.markdown("### ✅ Assessment Complete")

                # Decision section with color coding
                decision = response.get('decision')

                if decision == "Eligible":
                    st.markdown("""
                        <div class='success-card'>
                        <h3>🎉 Eligible for Loan</h3>
                        <p>Congratulations! You are eligible for the loan. A loan officer will contact you shortly to process your application.</p>
                        </div>
                    """, unsafe_allow_html=True)

                elif decision == "Needs Manual Review":
                    st.markdown("""
                        <div class='warning-card'>
                        <h3>⚠️ Manual Review Required</h3>
                        <p>Your application meets some but not all criteria. A loan officer will review your case for possible approval.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class='error-card'>
                        <h3>❌ Not Eligible</h3>
                        <p>Your application does not meet the current eligibility criteria. Review the recommendations below to improve your profile.</p>
                        </div>
                    """, unsafe_allow_html=True)

                # Download button
                col_download1, col_download2 = st.columns([2, 1])
                with col_download1:
                    st.download_button(
                        label="📥 Download Assessment Report (PDF)",
                        data=pdf_buffer,
                        file_name=f"loan_assessment_{data['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                st.divider()

                # Credit metrics
                st.markdown("### 📊 Credit Assessment Metrics")

                metric_col1, metric_col2, metric_col3 = st.columns(3)

                with metric_col1:
                    score_status = "GOOD ✓" if credit_score >= 700 else "NEEDS IMPROVEMENT ⚠"
                    score_color = "#28a745" if credit_score >= 700 else "#ffc107"
                    st.metric(
                        "Credit Score",
                        f"{credit_score}/1000",
                        delta=score_status,
                        delta_color="off"
                    )
                    st.markdown(f"<p style='color: {score_color}; font-weight: bold;'>{score_status}</p>", unsafe_allow_html=True)

                with metric_col2:
                    new_emi = response.get('new_emi', 0)
                    st.metric(
                        "Estimated New EMI",
                        f"₹ {new_emi:,.0f}",
                        delta=f"Total: ₹ {new_emi + existing_emi:,.0f}/month"
                    )

                with metric_col3:
                    emi_ratio = response.get('emi_ratio', 0)
                    ratio_status = "✓ Good" if emi_ratio <= 0.40 else "⚠ High"
                    st.metric(
                        "EMI-to-Income Ratio",
                        f"{emi_ratio:.1%}",
                        delta=ratio_status
                    )

                st.divider()

                # Eligibility assessment
                st.markdown("### ✓ Eligibility Assessment")
                for i, reason in enumerate(response.get("reasoning", []), 1):
                    st.markdown(f"**{i}.** {reason}")

                st.divider()

                # Recommendations
                st.markdown("### 💡 Improvement Recommendations")
                recommendations = get_recommendations(response, credit_score, data)

                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.info(f"**{i}.** {rec}")
                else:
                    st.success("🎉 No improvements needed! Your profile is excellent.")

                # Supporting evidence
                if response.get("rag_evidence"):
                    st.divider()
                    st.markdown("### 📚 Supporting Policy References")
                    for d in response.get("rag_evidence", []):
                        with st.expander(f"📖 {d.get('id', 'Policy Reference')}"):
                            st.write(d.get('content', ''))

            except requests.exceptions.Timeout:
                st.markdown("""
                    <div class='error-card'>
                    <h3>⏱️ Request Timeout</h3>
                    <p>The evaluation took too long. Please try again.</p>
                    </div>
                """, unsafe_allow_html=True)

            except requests.exceptions.ConnectionError:
                st.markdown("""
                    <div class='error-card'>
                    <h3>🔌 Connection Error</h3>
                    <p>Cannot reach the evaluation service. Make sure the backend is running on port 8000.</p>
                    </div>
                """, unsafe_allow_html=True)

            except requests.RequestException as e:
                st.markdown(f"""
                    <div class='error-card'>
                    <h3>❌ Error</h3>
                    <p>Service error: {str(e)}</p>
                    </div>
                """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
    <div class='info-box'>
    <small>
    <strong>Disclaimer:</strong> This is an automated assessment tool. All decisions are subject to manual review by a loan officer.
    The eligibility determination is based on the information provided and may be subject to verification.
    </small>
    </div>
""", unsafe_allow_html=True)
