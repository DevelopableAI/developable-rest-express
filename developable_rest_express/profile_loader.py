from __future__ import annotations

from pathlib import Path

import yaml

from .models import ConventionProfile


def load_profile(path: str | Path) -> ConventionProfile:
    profile_path = Path(path)
    data = yaml.safe_load(profile_path.read_text())
    return ConventionProfile.model_validate(data)
