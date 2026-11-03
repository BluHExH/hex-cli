from pathlib import Path

import hex_cli


def test_pyproject_version_matches_runtime():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{hex_cli.__version__}"' in text
