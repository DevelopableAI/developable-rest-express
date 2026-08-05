from __future__ import annotations

from .models import ConfidenceBucket, ConventionAssessment, ConventionEvidence


DEFAULT_CONFIDENCE_WEIGHTS = {
    "agreement": 0.35,
    "signal_strength": 0.25,
    "repo_quality": 0.15,
    "coverage": 0.15,
    "determinism_bonus": 0.10,
}

SIGNAL_STRENGTH_WEIGHTS = {
    "parser_match_rate": 0.30,
    "structural_match_rate": 0.20,
    "independent_detector_agreement": 0.20,
    "test_evidence_rate": 0.15,
    "ambiguity_rate": 0.15,
}


def compute_signal_strength(evidence: ConventionEvidence) -> float:
    metrics = evidence.detector_metrics
    score = (
        metrics.parser_match_rate * SIGNAL_STRENGTH_WEIGHTS["parser_match_rate"]
        + metrics.structural_match_rate * SIGNAL_STRENGTH_WEIGHTS["structural_match_rate"]
        + metrics.independent_detector_agreement
        * SIGNAL_STRENGTH_WEIGHTS["independent_detector_agreement"]
        + metrics.test_evidence_rate * SIGNAL_STRENGTH_WEIGHTS["test_evidence_rate"]
        + (1.0 - metrics.ambiguity_rate) * SIGNAL_STRENGTH_WEIGHTS["ambiguity_rate"]
    )
    return round(score, 4)


def determinism_bonus(source_type: str) -> float:
    if source_type == "deterministic":
        return 1.0
    if source_type == "manual":
        return 0.6
    return 0.25


def compute_confidence(evidence: ConventionEvidence) -> float:
    signal_strength = compute_signal_strength(evidence)
    score = (
        evidence.agreement * DEFAULT_CONFIDENCE_WEIGHTS["agreement"]
        + signal_strength * DEFAULT_CONFIDENCE_WEIGHTS["signal_strength"]
        + evidence.repo_quality * DEFAULT_CONFIDENCE_WEIGHTS["repo_quality"]
        + evidence.coverage * DEFAULT_CONFIDENCE_WEIGHTS["coverage"]
        + determinism_bonus(evidence.source_type)
        * DEFAULT_CONFIDENCE_WEIGHTS["determinism_bonus"]
        - evidence.conflict_penalty
    )
    return round(min(max(score, 0.0), 1.0), 4)


def bucket_confidence(confidence: float) -> ConfidenceBucket:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    if confidence >= 0.40:
        return "low"
    return "do_not_operationalize"


def assess_convention(evidence: ConventionEvidence) -> ConventionAssessment:
    signal_strength = compute_signal_strength(evidence)
    confidence = compute_confidence(evidence)
    return ConventionAssessment(
        convention_name=evidence.convention_name,
        inferred_value=evidence.inferred_value,
        signal_strength=signal_strength,
        detector_metrics=evidence.detector_metrics,
        confidence=confidence,
        bucket=bucket_confidence(confidence),
        source_type=evidence.source_type,
        evidence=evidence.evidence,
        affected_repos=evidence.affected_repos,
        conflicts=evidence.conflicts,
        coverage=evidence.coverage,
        supported=evidence.supported,
        ambiguous=evidence.ambiguous,
    )
