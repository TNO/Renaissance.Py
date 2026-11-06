# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the ruff helpers that clean up and format the files a recipe changed."""

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from hamcrest import assert_that, equal_to

from renaissance.utils.ruff_utils import run_ruff_format, run_ruff_import_cleanup

UNUSED_IMPORT = ("import os\nimport sys\n\nprint(sys.argv)\n", "import sys\n\nprint(sys.argv)\n")
UNSORTED_IMPORTS = ("import sys\nimport os\n\nprint(os, sys)\n", "import os\nimport sys\n\nprint(os, sys)\n")
NOTHING_TO_FIX = ("import os\n\nprint(os)\n", "import os\n\nprint(os)\n")
UNFORMATTED = ("x = {  'a':1 }\n", 'x = {"a": 1}\n')
LONG_SIGNATURE = (
    "def f[T](first: list[T], second: list[T]) -> T: ...\n",
    "def f[T](\n    first: list[T], second: list[T]\n) -> T: ...\n",
)
ALREADY_FORMATTED = ('x = {"a": 1}\n', 'x = {"a": 1}\n')


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


@pytest.mark.parametrize(
    "cases",
    [
        pytest.param([UNFORMATTED], id="unformatted"),
        pytest.param([LONG_SIGNATURE], id="long_signature"),
        pytest.param([ALREADY_FORMATTED], id="already_formatted"),
        pytest.param([UNFORMATTED, LONG_SIGNATURE], id="several_files"),
    ],
)
def test_formats_each_file(tmp_path: Path, cases: list[tuple[str, str]]) -> None:
    """Each file is rewritten in the ruff format style, with the line length of the ruff settings next to it."""
    (tmp_path / "ruff.toml").write_text("line-length = 40\n", encoding="utf-8")
    paths = [tmp_path / f"module_{index}.py" for index in range(len(cases))]
    for path, (source, _) in zip(paths, cases, strict=True):
        path.write_text(source, encoding="utf-8")

    run_ruff_format(paths)

    assert_that([path.read_text(encoding="utf-8") for path in paths], equal_to([expected for _, expected in cases]))


@pytest.mark.parametrize(
    ("ruff_helper", "source"),
    [
        pytest.param(run_ruff_import_cleanup, UNUSED_IMPORT[0], id="import_cleanup"),
        pytest.param(run_ruff_format, UNFORMATTED[0], id="format"),
    ],
)
def test_no_paths_changes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ruff_helper: Callable[[Sequence[Path]], None],
    source: str,
) -> None:
    """An empty list leaves the files in the working directory untouched."""
    path = tmp_path / "module.py"
    path.write_text(source, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    ruff_helper([])

    assert_that(path.read_text(encoding="utf-8"), equal_to(source))
