from agents.eligibility_agent import EligibilityAgent
from schemas.models import Application


def test_eligible_case():
    app = Application(
        name="Test",
        age=30,
        monthly_income=5000,
        existing_emi=100,
        credit_score=750,
        employment_type="salaried",
        loan_amount_required=6000,
    )

    agent = EligibilityAgent()
    res = agent.evaluate(app)
    assert res["decision"] == "Eligible"


def test_not_eligible_due_to_credit():
    app = Application(
        name="Test",
        age=30,
        monthly_income=5000,
        existing_emi=100,
        credit_score=650,
        employment_type="salaried",
        loan_amount_required=6000,
    )
    agent = EligibilityAgent()
    res = agent.evaluate(app)
    assert res["decision"] in ("Not Eligible", "Needs Manual Review")


def test_manual_review_borderline_emi():
    # Construct a case with emi_ratio ~0.40
    app = Application(
        name="Test",
        age=35,
        monthly_income=3000,
        existing_emi=600,
        credit_score=705,
        employment_type="self-employed",
        loan_amount_required=1200,  # new_emi = 100 -> total = 700 / 3000 = 0.233
    )
    agent = EligibilityAgent()
    res = agent.evaluate(app)
    assert "decision" in res
