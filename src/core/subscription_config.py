# src/core/subscription_config.py
#
# Central configuration for user plan constraints.
# All tier limits live here — change once, applies everywhere.

from typing import TypedDict


class PlanConstraints(TypedDict):
    max_pages: int
    max_tokens_4h: int
    max_reference_pages: int


PLAN_CONSTRAINTS: dict[str, PlanConstraints] = {
    "free": {
        "max_pages": 10,
        "max_tokens_4h": 50_000,
        "max_reference_pages": 5,
    },
    "premium": {
        "max_pages": 50,
        "max_tokens_4h": 250_000,
        "max_reference_pages": 100,
    },
}

# Default to free plan constraints if a plan is unrecognised.
DEFAULT_PLAN = "free"


def get_plan_constraints(plan: str) -> PlanConstraints:
    """
    Return the constraints for the given plan name.
    Falls back to 'free' if the plan is unrecognised.
    """
    return PLAN_CONSTRAINTS.get(plan, PLAN_CONSTRAINTS[DEFAULT_PLAN])
