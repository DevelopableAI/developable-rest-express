"""developable-rest-express package."""

from .analysis import analyze_profile
from .benchmark_loader import load_benchmark
from .evaluation import evaluate_benchmark
from .models import (
    AnalysisReport,
    BenchmarkFixture,
    ComparisonResult,
    ConventionAssessment,
    ConventionEvidence,
    ConventionExpectation,
    ConventionProfile,
    DetectorMetrics,
    EvaluationResult,
    RepoHandle,
    RepoReference,
)
from .profile_loader import load_profile
from .scoring import bucket_confidence, compute_confidence, compute_signal_strength

__all__ = [
    "AnalysisReport",
    "BenchmarkFixture",
    "ComparisonResult",
    "ConventionAssessment",
    "ConventionEvidence",
    "ConventionExpectation",
    "ConventionProfile",
    "DetectorMetrics",
    "EvaluationResult",
    "RepoHandle",
    "RepoReference",
    "analyze_profile",
    "evaluate_benchmark",
    "load_benchmark",
    "load_profile",
    "compute_signal_strength",
    "compute_confidence",
    "bucket_confidence",
]
