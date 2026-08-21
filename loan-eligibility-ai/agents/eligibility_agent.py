"""Eligibility Agent

This module implements the core eligibility rules as a simple agent-like class.
Keep logic deterministic and unit-testable.
"""

from typing import Dict, Any
from schemas.models import Application


class EligibilityAgent:
    """Encapsulates loan eligibility business rules.

    Methods return a structured result describing each rule and a final decision.
    """

    STABLE_EMPLOYMENT = {"salaried", "govt"}

    def evaluate(self, app: Application) -> Dict[str, Any]:
        # New EMI estimation: simple conservative estimate = loan / 12 months
        # (POC simplification; replace with amortization for production)
        new_emi = round(app.loan_amount_required / 12.0, 2)

        emi_ratio = 0.0
        if app.monthly_income > 0:
            emi_ratio = round((app.existing_emi + new_emi) / app.monthly_income, 4)

        results = []

        # Credit score rule: must exceed 700
        credit_pass = app.credit_score > 700
        results.append({
            "rule": "credit_score",
            "passed": credit_pass,
            "value": app.credit_score,
            "note": "credit score must exceed 700",
        })

        # Age rule
        age_pass = 21 <= app.age <= 60
        results.append({
            "rule": "age",
            "passed": age_pass,
            "value": app.age,
            "note": "age must be between 21 and 60",
        })

        # Employment rule (improves eligibility but not strictly required)
        employment_stable = app.employment_type in self.STABLE_EMPLOYMENT
        results.append({
            "rule": "employment",
            "passed": employment_stable,
            "value": app.employment_type,
            "note": "stable employment improves eligibility",
        })

        # EMI-to-income ratio rule
        emi_pass = emi_ratio <= 0.40
        results.append({
            "rule": "emi_ratio",
            "passed": emi_pass,
            "value": emi_ratio,
            "note": "(existing EMI + new EMI) / income should be <= 0.40",
        })

        # Decision logic with a small 'borderline' tolerance
        borderline = False
        # Borderline credit near threshold
        if 690 <= app.credit_score <= 710:
            borderline = True

        # Borderline emi ratio near threshold
        if 0.38 <= emi_ratio <= 0.42:
            borderline = True

        # If any critical rule fails -> not eligible
        critical_fail = not credit_pass or not age_pass or not emi_pass

        if critical_fail and not borderline:
            decision = "Not Eligible"
        elif critical_fail and borderline:
            decision = "Needs Manual Review"
        else:
            # All critical rules pass — improve if employment is stable
            decision = "Eligible" if (credit_pass and age_pass and emi_pass) else "Needs Manual Review"

        return {
            "decision": decision,
            "new_emi": new_emi,
            "emi_ratio": emi_ratio,
            "rule_results": results,
        }
