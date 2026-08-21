from pydantic import BaseModel, Field, validator
from typing import Literal


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
