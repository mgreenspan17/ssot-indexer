"""OS layer package for SSOT OS governance, routing, compute, and diagnostics.

Assumptions:
- Governance source is provided externally via /registry/agent-governance or the canonical file.
- Modules must remain importable without performing side effects.

Boundaries:
- No module in this package executes deployment or service restarts at import time.

Integration notes:
- Other agents should import these modules for planning, validation, and structured decisions only.
"""

from .governance_loader import GovernanceDocument, load_governance
from .governance_validator import GovernanceValidationResult, validate_governance_document

__all__ = [
    "GovernanceDocument",
    "GovernanceValidationResult",
    "load_governance",
    "validate_governance_document",
]
