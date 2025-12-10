"""
Orchestrators for ASP multi-agent workflows.

Orchestrators coordinate multiple agents with feedback loops,
implementing phase-aware error correction per PSP/TSP principles.
"""

from asp.orchestrators.confidence import (
    ConfidenceBreakdown,
    calculate_confidence,
    calculate_diagnostic_confidence,
    calculate_fix_confidence,
    calculate_iteration_penalty,
    calculate_test_coverage_confidence,
)
from asp.orchestrators.hitl_config import (
    AUTONOMOUS_CONFIG,
    CONSERVATIVE_CONFIG,
    DEFAULT_CONFIG,
    PRODUCTION_CONFIG,
    SUPERVISED_CONFIG,
    HITLConfig,
)
from asp.orchestrators.planning_design_orchestrator import PlanningDesignOrchestrator
from asp.orchestrators.repair_orchestrator import (
    ApprovalCallback,
    DiagnosticFailed,
    HumanRejectedRepair,
    MaxIterationsExceeded,
    RepairError,
    RepairOrchestrator,
    RepairRequest,
)
from asp.orchestrators.tsp_orchestrator import TSPOrchestrator
from asp.orchestrators.types import PlanningDesignResult, TSPExecutionResult

__all__ = [
    # Planning/Design
    "PlanningDesignOrchestrator",
    "PlanningDesignResult",
    # TSP
    "TSPOrchestrator",
    "TSPExecutionResult",
    # Repair Orchestration (ADR 006)
    "RepairOrchestrator",
    "RepairRequest",
    "RepairError",
    "MaxIterationsExceeded",
    "HumanRejectedRepair",
    "DiagnosticFailed",
    "ApprovalCallback",
    # Confidence Calculation
    "ConfidenceBreakdown",
    "calculate_confidence",
    "calculate_diagnostic_confidence",
    "calculate_fix_confidence",
    "calculate_test_coverage_confidence",
    "calculate_iteration_penalty",
    # HITL Configuration
    "HITLConfig",
    "DEFAULT_CONFIG",
    "AUTONOMOUS_CONFIG",
    "SUPERVISED_CONFIG",
    "CONSERVATIVE_CONFIG",
    "PRODUCTION_CONFIG",
]
