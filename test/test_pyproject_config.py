"""Guard against the source-root list drifting between tool configs.

pyproject.toml has no way to declare `["src", "test", "features"]` once and
reuse it (TOML has no anchors/references), so the same list is duplicated in
[tool.pytest.ini_options] pythonpath, [tool.ruff] src, and
[tool.pyright] extraPaths. This test fails loudly if one of them is updated
without updating the others.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_pyproject() -> dict:
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_source_roots_are_consistent_across_tool_configs():
    config = _load_pyproject()
    pytest_pythonpath = config["tool"]["pytest"]["ini_options"]["pythonpath"]
    ruff_src = config["tool"]["ruff"]["src"]
    pyright_extra_paths = config["tool"]["pyright"]["extraPaths"]

    assert pytest_pythonpath == ruff_src == pyright_extra_paths, (
        "The source-root list ['src', 'test', 'features'] must be kept in sync across "
        "[tool.pytest.ini_options].pythonpath, [tool.ruff].src, and [tool.pyright].extraPaths "
        "in pyproject.toml."
    )
