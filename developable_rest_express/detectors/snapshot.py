from __future__ import annotations

import json
import re
from functools import cached_property
from pathlib import Path
from typing import List, Set

from .base import ratio


CODE_SUFFIXES = frozenset({".ts", ".js", ".mjs", ".cjs"})
IGNORED_DIRECTORIES = frozenset({".git", "node_modules", "dist", "build", "coverage"})
ROUTE_DIRECTORIES = frozenset({"routes", "route", "router", "routers"})
TEST_DIRECTORIES = frozenset({"test", "tests", "__tests__"})
TEST_FILE_SUFFIXES = (".spec.ts", ".spec.js", ".test.ts", ".test.js")

ROUTE_METHOD_PATTERN = re.compile(r"\b(app|router)\.(get|post|put|delete|patch|options|head)\(")
IMPORT_PATTERN = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
ROUTE_DECORATOR_PATTERN = re.compile(r"@(?:Json)?Controller\(")
ROUTER_CONSTRUCTORS = ("express.Router", "Router()")

MINIMUM_TEST_SIGNAL = 0.3


class RepoSnapshot:
    """Cached view of the files that the Express detectors read.

    The snapshot walks the repository once during construction, then answers
    content and structure questions from memory so that each file is read from
    disk at most once per analysis however many detectors consult it.

    Attributes:
        root: Repository root directory.
        code_files: Every non-vendored JavaScript or TypeScript source file.
        test_files: Subset of ``code_files`` living in a test directory or
            carrying a test filename suffix.
        route_files: Subset of ``code_files`` that appear to declare routes.
        package_data: Parsed ``package.json`` contents, empty when the file is
            absent or unparseable.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self._text_cache: dict[Path, str] = {}
        self._imports_cache: dict[Path, List[str]] = {}
        self._package_root_cache: dict[Path, Path | None] = {}
        self.code_files = self._collect_code_files()
        self.test_files = [path for path in self.code_files if self._is_test_file(path)]
        self.package_data = self._load_package_json()
        self.route_files = [path for path in self.code_files if self._declares_routes(path)]

    def text(self, path: Path) -> str:
        """Return the decoded contents of ``path``, empty when unreadable."""
        if path not in self._text_cache:
            try:
                self._text_cache[path] = path.read_text(errors="ignore")
            except OSError:
                self._text_cache[path] = ""
        return self._text_cache[path]

    def imports_in(self, path: Path) -> List[str]:
        """Return every module specifier imported or required by ``path``."""
        if path not in self._imports_cache:
            matches = IMPORT_PATTERN.findall(self.text(path))
            self._imports_cache[path] = [item for match in matches for item in match if item]
        return self._imports_cache[path]

    def relative_parts(self, path: Path) -> Set[str]:
        """Return lowercased path components measured from the snapshot root.

        This deliberately differs from :meth:`directory_count`, which measures
        from the nearest ancestor holding a ``package.json``. The two disagree
        inside nested packages, and detectors depend on that difference.
        """
        return {part.lower() for part in path.relative_to(self.root).parts}

    def directory_count(self, name: str) -> int:
        """Count code files whose package-relative path contains ``name``.

        Paths are measured from the nearest ancestor directory holding a
        ``package.json`` rather than from the snapshot root, so files inside a
        nested package are scoped to their own manifest.
        """
        return sum(name in self._package_relative_parts(path) for path in self.code_files)

    def has_root_config(self, stem: str) -> bool:
        """Return whether a ``<stem>.*`` config file sits at the repository root.

        Only the root directory is searched, unlike the recursive walk backing
        :attr:`code_files`.
        """
        return any(path.name.startswith(stem) for path in self.root.glob(f"{stem}.*"))

    @cached_property
    def route_file_set(self) -> frozenset[Path]:
        """Return :attr:`route_files` as a set, for membership tests."""
        return frozenset(self.route_files)

    @cached_property
    def package_text(self) -> str:
        """Return ``package.json`` re-serialized as lowercase JSON text."""
        return json.dumps(self.package_data).lower()

    @cached_property
    def test_signal(self) -> float:
        """Return the shared test-evidence rate used by most detectors.

        The floor is a scoring judgement rather than a fact about the files.
        It lives here because five detectors apply it identically, and one
        shared definition is worth more than strict purity.
        """
        if not self.test_files:
            return 0.0
        files_using_supertest = sum("supertest" in self.text(path) for path in self.test_files)
        return max(
            MINIMUM_TEST_SIGNAL,
            ratio(files_using_supertest + len(self.test_files), len(self.test_files) * 2),
        )

    def _collect_code_files(self) -> List[Path]:
        return [
            path
            for path in self.root.rglob("*")
            if path.is_file()
            and not IGNORED_DIRECTORIES.intersection(path.parts)
            and path.suffix in CODE_SUFFIXES
        ]

    def _is_test_file(self, path: Path) -> bool:
        parts = path.relative_to(self.root).parts
        return any(part in TEST_DIRECTORIES for part in parts) or path.name.endswith(TEST_FILE_SUFFIXES)

    def _declares_routes(self, path: Path) -> bool:
        if ROUTE_DIRECTORIES & self.relative_parts(path):
            return True
        text = self.text(path)
        return (
            any(marker in text for marker in ROUTER_CONSTRUCTORS)
            or bool(ROUTE_METHOD_PATTERN.search(text))
            or bool(ROUTE_DECORATOR_PATTERN.search(text))
        )

    def _load_package_json(self) -> dict[str, object]:
        package_path = self.root / "package.json"
        if not package_path.exists():
            return {}
        try:
            return json.loads(package_path.read_text())
        except json.JSONDecodeError:
            return {}

    def _package_relative_parts(self, path: Path) -> Set[str]:
        package_root = self._package_root_for(path)
        parts = path.relative_to(package_root).parts if package_root else path.parts
        return {part.lower() for part in parts}

    def _package_root_for(self, path: Path) -> Path | None:
        if path not in self._package_root_cache:
            self._package_root_cache[path] = self._find_package_root(path)
        return self._package_root_cache[path]

    @staticmethod
    def _find_package_root(path: Path) -> Path | None:
        for parent in [path, *path.parents]:
            if (parent / "package.json").exists():
                return parent
        return None
