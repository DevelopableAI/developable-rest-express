from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


InferenceScopeItem = Literal[
    "routes",
    "validation",
    "auth",
    "data_access",
    "testing",
    "ci_commands",
    "error_contract",
    "runtime",
]

ConventionTarget = Literal[
    "route_declaration_style",
    "route_controller_boundary",
    "validation_at_edge_pattern",
    "service_repository_layering",
    "auth_middleware_presence",
    "test_layout_shape",
]

SourceType = Literal["deterministic", "llm_assisted", "manual"]
ConfidenceBucket = Literal["high", "medium", "low", "do_not_operationalize"]
RepoSourceKind = Literal["local_path", "github_url"]
RepoRole = Literal["reference", "context", "evaluation"]
OutputFormat = Literal["json", "md", "both"]
ReviewMode = Literal["bootstrap_self_review", "peer_review"]


def _is_github_source(value: str) -> bool:
    normalized = value.strip()
    if normalized.startswith(("http://", "https://", "ssh://", "git://", "git@")):
        return True
    return "github.com/" in normalized


def _derive_repo_id(source: str) -> str:
    normalized = source.rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@github.com:"):
        normalized = normalized.split(":", 1)[1]
    parts = normalized.split("/")
    return parts[-1] if parts else normalized


class RepoMetadata(BaseModel):
    framework: str
    language: str
    maturity: Literal["gold", "silver", "bronze", "legacy"] = "silver"
    owner: Optional[str] = None
    last_active_date: Optional[str] = None


class RepoReference(BaseModel):
    repo_id: Optional[str] = None
    source: str
    revision: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, value: Any) -> Any:
        if isinstance(value, str):
            return {"source": value}
        return value

    @model_validator(mode="after")
    def finalize(self) -> "RepoReference":
        source = self.source.strip()
        if not source:
            raise ValueError("repo source must not be empty")
        self.source = source
        self.repo_id = (self.repo_id or _derive_repo_id(source)).strip()
        if not self.repo_id:
            raise ValueError("repo_id could not be derived from source")
        if self.revision is not None:
            self.revision = self.revision.strip().lower()
            if not re.fullmatch(r"[0-9a-f]{40}", self.revision):
                raise ValueError("revision must be a full 40-character Git commit SHA")
        return self

    @property
    def source_kind(self) -> RepoSourceKind:
        return "github_url" if _is_github_source(self.source) else "local_path"


class SafetyPolicy(BaseModel):
    require_approval: List[str] = Field(default_factory=list)


class ConventionProfile(BaseModel):
    profile_id: str
    library: Literal["developable-rest-express"]
    purpose: str
    reference_repos: List[RepoReference] = Field(min_length=2, max_length=10)
    context_repos: List[RepoReference] = Field(default_factory=list)
    repo_metadata: Dict[str, RepoMetadata] = Field(default_factory=dict)
    inference_scope: List[InferenceScopeItem] = Field(default_factory=list)
    safety_policy: SafetyPolicy = Field(default_factory=SafetyPolicy)
    output_targets: List[str] = Field(default_factory=list)
    evaluation_set: List[RepoReference] = Field(default_factory=list)
    expected_framework: Optional[Literal["express"]] = None

    @model_validator(mode="after")
    def validate_profile(self) -> "ConventionProfile":
        self.profile_id = self.profile_id.strip()
        if not self.profile_id:
            raise ValueError("profile_id must not be empty")

        all_repos = self.reference_repos + self.context_repos + self.evaluation_set
        repo_ids = [repo.repo_id for repo in all_repos]
        if len(repo_ids) != len(set(repo_ids)):
            raise ValueError("duplicate repo_id detected across profile repo inputs")

        for repo_id in self.repo_metadata:
            if repo_id not in set(repo_ids):
                raise ValueError(f"repo_metadata entry '{repo_id}' does not map to a declared repo")
        return self


class DetectorMetrics(BaseModel):
    parser_match_rate: float = Field(ge=0.0, le=1.0)
    structural_match_rate: float = Field(ge=0.0, le=1.0)
    independent_detector_agreement: float = Field(ge=0.0, le=1.0)
    test_evidence_rate: float = Field(ge=0.0, le=1.0)
    ambiguity_rate: float = Field(ge=0.0, le=1.0)


class RepoHandle(BaseModel):
    repo_id: str
    source: str
    source_kind: RepoSourceKind
    role: RepoRole
    local_path: str
    requested_revision: Optional[str] = None
    commit_sha: Optional[str] = None
    framework: Optional[str] = None
    language: Optional[str] = None
    prepared_from_cache: bool = False
    notes: List[str] = Field(default_factory=list)

    @property
    def local_path_obj(self) -> Path:
        return Path(self.local_path)


class ConventionEvidence(BaseModel):
    convention_name: ConventionTarget
    inferred_value: str
    source_type: SourceType = "deterministic"
    agreement: float = Field(ge=0.0, le=1.0)
    repo_quality: float = Field(ge=0.0, le=1.0)
    coverage: float = Field(ge=0.0, le=1.0)
    conflict_penalty: float = Field(ge=0.0, le=1.0)
    detector_metrics: DetectorMetrics
    evidence: List[str] = Field(default_factory=list)
    affected_repos: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    supported: bool = True
    ambiguous: bool = False


class ConventionAssessment(BaseModel):
    convention_name: ConventionTarget
    inferred_value: str
    signal_strength: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    bucket: ConfidenceBucket
    source_type: SourceType
    evidence: List[str] = Field(default_factory=list)
    affected_repos: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    coverage: float = Field(ge=0.0, le=1.0)
    supported: bool = True
    ambiguous: bool = False


class RepoAnalysis(BaseModel):
    repo: RepoHandle
    conventions: List[ConventionAssessment] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    profile_id: str
    library: Literal["developable-rest-express"]
    expected_framework: Optional[Literal["express"]] = None
    repos: List[RepoHandle]
    repo_reports: List[RepoAnalysis]
    summary: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class ConventionExpectation(BaseModel):
    route_declaration_style: str
    route_controller_boundary: str
    validation_at_edge_pattern: str
    service_repository_layering: str
    auth_middleware_presence: str
    test_layout_shape: str

    def for_target(self, target: ConventionTarget) -> str:
        return getattr(self, target)


class BenchmarkReview(BaseModel):
    author: str
    reviewer: str
    review_mode: ReviewMode
    reviewed_at: date
    rationale: str

    @model_validator(mode="after")
    def validate_review(self) -> "BenchmarkReview":
        self.author = self.author.strip()
        self.reviewer = self.reviewer.strip()
        self.rationale = self.rationale.strip()
        if not self.author or not self.reviewer:
            raise ValueError("benchmark review author and reviewer must not be empty")
        if not self.rationale:
            raise ValueError("benchmark review rationale must not be empty")
        return self


class BenchmarkGovernance(BaseModel):
    review_mode: ReviewMode
    maintainers: List[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_governance(self) -> "BenchmarkGovernance":
        self.maintainers = [maintainer.strip() for maintainer in self.maintainers if maintainer.strip()]
        if not self.maintainers:
            raise ValueError("benchmark governance requires at least one maintainer")
        if len(set(self.maintainers)) != len(self.maintainers):
            raise ValueError("benchmark governance maintainers must be unique")
        if self.review_mode == "bootstrap_self_review" and len(self.maintainers) != 1:
            raise ValueError("bootstrap_self_review requires exactly one maintainer")
        return self


class BenchmarkFixture(BaseModel):
    benchmark_id: str
    library: Literal["developable-rest-express"]
    framework_scope: Literal["express"]
    repos: List[RepoReference] = Field(min_length=1)
    expected_conventions: Dict[str, ConventionExpectation]
    review: BenchmarkReview
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_fixture(self) -> "BenchmarkFixture":
        self.benchmark_id = self.benchmark_id.strip()
        if not self.benchmark_id:
            raise ValueError("benchmark_id must not be empty")

        repo_ids = [repo.repo_id for repo in self.repos]
        if len(repo_ids) != len(set(repo_ids)):
            raise ValueError("duplicate repo_id detected in benchmark repos")

        missing = set(repo_ids) - set(self.expected_conventions)
        unknown = set(self.expected_conventions) - set(repo_ids)
        if missing:
            raise ValueError(f"missing expected_conventions for repo ids: {sorted(missing)}")
        if unknown:
            raise ValueError(f"expected_conventions contains unknown repo ids: {sorted(unknown)}")
        missing_revisions = [repo.repo_id for repo in self.repos if repo.source_kind == "github_url" and not repo.revision]
        if missing_revisions:
            raise ValueError(f"GitHub benchmark repos require revisions: {missing_revisions}")
        return self


class ComparisonResult(BaseModel):
    repo_id: str
    convention_name: ConventionTarget
    expected_value: str
    inferred_value: str
    matched: bool
    confidence: float
    bucket: ConfidenceBucket
    supported: bool
    ambiguous: bool


class EvaluationResult(BaseModel):
    benchmark_id: str
    library: Literal["developable-rest-express"]
    framework_scope: Literal["express"]
    review: BenchmarkReview
    repos: List[RepoHandle]
    comparisons: List[ComparisonResult]
    total_conventions_evaluated: int
    exact_match_accuracy_by_convention: Dict[str, float]
    precision_by_confidence_bucket: Dict[str, float]
    ambiguous_repo_count: int
    unsupported_convention_count: int
    false_positives: List[ComparisonResult] = Field(default_factory=list)
    false_negatives: List[ComparisonResult] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
