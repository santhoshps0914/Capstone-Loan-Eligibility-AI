from pydantic import BaseModel, Field, validator
from typing import Dict, List, Literal, Optional


class Application(BaseModel):
    name: str = Field(..., example="Alice")
    age: int = Field(..., ge=0, example=30)
    monthly_income: float = Field(..., gt=0, example=5000)
    existing_emi: float = Field(..., ge=0, example=200)
    credit_score: int = Field(..., ge=0, le=1000, example=720)
    employment_type: Literal["salaried", "self-employed", "govt", "other"] = Field(..., example="salaried")
    loan_amount_required: float = Field(..., gt=0, example=10000)

    @validator("age")
    def age_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("age must be positive")
        return v


class ChatTurn(BaseModel):
    """One prior message in the chat transcript."""

    role: Literal["user", "assistant"] = Field(..., example="user")
    content: str = Field(..., min_length=1, max_length=2000, example="What credit score do I need?")


class AssessmentContext(BaseModel):
    """The applicant's latest assessment, so the chatbot can explain it.

    Every field is optional — the chatbot answers general questions with no
    context at all. The applicant's name is deliberately absent: explaining a
    result never needs it, so it does not travel down the chat path.
    """

    decision: Optional[str] = Field(None, example="Needs Manual Review")
    credit_score: Optional[int] = Field(None, ge=0, le=1000, example=695)
    emi_ratio: Optional[float] = Field(None, ge=0, example=0.41)
    new_emi: Optional[float] = Field(None, ge=0, example=15000)
    age: Optional[int] = Field(None, ge=0, example=35)
    employment_type: Optional[str] = Field(None, example="salaried")
    reasoning: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, example="What credit score do I need?")
    history: List[ChatTurn] = Field(default_factory=list)
    context: Optional[AssessmentContext] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]] = Field(default_factory=list)
    mode: Literal["rules", "llm"] = Field(..., example="rules")
    suggestions: List[str] = Field(default_factory=list)


class ChatInfoResponse(BaseModel):
    llm_enabled: bool = Field(..., example=False)
    suggested_questions: List[str] = Field(default_factory=list)
