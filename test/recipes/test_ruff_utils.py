# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the ruff import cleanup helper."""

from pathlib import Path

import pytest
from hamcrest import assert_that, equal_to

from renaissance.recipes.ruff_utils import run_ruff_import_cleanup

UNUSED_IMPORT = ("import os\nimport sys\n\nprint(sys.argv)\n", "import sys\n\nprint(sys.argv)\n")
UNSORTED_IMPORTS = ("import sys\nimport os\n\nprint(os, sys)\n", "import os\nimport sys\n\nprint(os, sys)\n")
NOTHING_TO_FIX = ("import os\n\nprint(os)\n", "import os\n\nprint(os)\n")


@pytest.mark.parametrize(
    "cases",
    [
        pytest.param([UNUSED_IMPORT], id="unused_import"),
        pytest.param([UNSORTED_IMPORTS], id="unsorted_imports"),
        pytest.param([NOTHING_TO_FIX], id="nothing_to_fix"),
        pytest.param([UNUSED_IMPORT, UNSORTED_IMPORTS], id="several_files"),
    ],
)
def test_cleans_up_the_imports_of_each_file(tmp_path: Path, cases: list[tuple[str, str]]) -> None:
    """Each file loses its unused imports and gets its imports sorted."""
    paths = [tmp_path / f"module_{index}.py" for index in range(len(cases))]
    for path, (source, _) in zip(paths, cases, strict=True):
        path.write_text(source, encoding="utf-8")

    run_ruff_import_cleanup(paths)

    assert_that([path.read_text(encoding="utf-8") for path in paths], equal_to([expected for _, expected in cases]))


def test_no_paths_changes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty list leaves the files in the working directory untouched."""
    source, _ = UNUSED_IMPORT
    path = tmp_path / "module.py"
    path.write_text(source, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    run_ruff_import_cleanup([])

    assert_that(path.read_text(encoding="utf-8"), equal_to(source))
