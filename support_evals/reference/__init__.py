"""Synthetic support operation used for local demos and regression tests."""

from .shop import (
    BrokenReferenceAdapter,
    REFERENCE_SCENARIOS,
    ReferenceShopAdapter,
    SafeReferenceAdapter,
    apply_mutation,
    reference_scenarios,
)

__all__ = [
    "BrokenReferenceAdapter", "REFERENCE_SCENARIOS", "ReferenceShopAdapter",
    "SafeReferenceAdapter", "apply_mutation", "reference_scenarios",
]
