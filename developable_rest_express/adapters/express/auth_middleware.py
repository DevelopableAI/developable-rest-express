from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...models import ConventionTarget, DetectorMetrics
from .base import Classification, Detector, DetectorFinding, ratio
from .snapshot import RepoSnapshot


AUTH_HINTS = ("auth", "authenticate", "passport", "jwt", "requireauth", "require-auth")

AUTH_PRESENT = "auth_middleware_present"
AUTH_UNCLEAR = "auth_middleware_unclear"


def _looks_like_auth(value: str) -> bool:
    """Return whether ``value`` mentions a known authentication marker."""
    lowered = value.lower()
    return any(hint in lowered for hint in AUTH_HINTS)


@dataclass(frozen=True)
class AuthSignals:
    """Counts of authentication markers observed in one repository.

    Attributes:
        auth_file_names: Source files whose name mentions authentication.
        route_auth_imports: Imports in route files that look authentication
            related.
        middleware_directories: Code files sitting under a middleware directory.
    """

    auth_file_names: int
    route_auth_imports: int
    middleware_directories: int


class AuthMiddlewareDetector(Detector):
    """Detect whether authentication is applied as route middleware."""

    convention_name: ClassVar[ConventionTarget] = "auth_middleware_presence"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({AUTH_UNCLEAR})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the authentication finding for ``snapshot``."""
        signals = self._gather(snapshot)
        classification = self._classify(signals)
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> AuthSignals:
        return AuthSignals(
            auth_file_names=sum(_looks_like_auth(path.name) for path in snapshot.code_files),
            route_auth_imports=sum(
                _looks_like_auth(specifier)
                for path in snapshot.route_files
                for specifier in snapshot.imports_in(path)
            ),
            middleware_directories=snapshot.directory_count("middleware"),
        )

    @staticmethod
    def _classify(signals: AuthSignals) -> Classification:
        if not (signals.route_auth_imports or signals.auth_file_names):
            return Classification(AUTH_UNCLEAR, 0.8)
        return Classification(AUTH_PRESENT, 0.15 if signals.route_auth_imports else 0.35)

    @staticmethod
    def _metrics(
        snapshot: RepoSnapshot,
        signals: AuthSignals,
        classification: Classification,
    ) -> DetectorMetrics:
        recognized = signals.middleware_directories + signals.auth_file_names
        return DetectorMetrics(
            parser_match_rate=ratio(
                signals.auth_file_names + signals.route_auth_imports,
                max(len(snapshot.route_files), 1) * 2,
            ),
            structural_match_rate=ratio(
                recognized,
                max(recognized + signals.route_auth_imports, 1),
            ),
            independent_detector_agreement=0.88 if classification.value == AUTH_PRESENT else 0.35,
            test_evidence_rate=snapshot.test_signal,
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: AuthSignals) -> tuple[str, ...]:
        return (
            f"Auth-related file names detected: {signals.auth_file_names}.",
            f"Route imports that look auth-related: {signals.route_auth_imports}.",
            f"Middleware directory signals: {signals.middleware_directories}.",
        )
