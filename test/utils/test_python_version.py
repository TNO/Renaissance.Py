"""Tests for find_nearest_pyproject and minimum_python_version."""

from pathlib import Path

from hamcrest import assert_that, is_

from renaissance.utils.python_version import find_nearest_pyproject, minimum_python_version


class TestFindNearestPyproject:
    """See module docstring."""

    def test_finds_pyproject_in_same_directory(self, tmp_path: Path) -> None:
        """AI: Verify a pyproject.toml in the same directory as the starting path is found directly."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        assert_that(find_nearest_pyproject(tmp_path), is_(tmp_path / "pyproject.toml"))

    def test_walks_up_to_parent_pyproject(self, tmp_path: Path) -> None:
        """AI: Verify the search walks up parent directories to find a pyproject.toml higher up."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        nested = tmp_path / "src" / "pkg"
        nested.mkdir(parents=True)
        assert_that(find_nearest_pyproject(nested), is_(tmp_path / "pyproject.toml"))

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when no pyproject.toml exists anywhere above the starting path."""
        assert_that(find_nearest_pyproject(tmp_path), is_(None))


class TestMinimumPythonVersion:
    """See module docstring."""

    def test_reads_lower_bound_specifier(self, tmp_path: Path) -> None:
        """AI: Verify a plain ">=" lower-bound specifier is read as the minimum version."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.12"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 12)))

    def test_reads_older_lower_bound(self, tmp_path: Path) -> None:
        """AI: Verify an older ">=" lower-bound specifier is read as the minimum version too."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 10)))

    def test_reads_exact_pin(self, tmp_path: Path) -> None:
        """AI: Verify an "==3.14.*" exact-minor pin is read as that minor version."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "==3.14.*"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 14)))

    def test_none_when_no_pyproject(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when no pyproject.toml is found at all."""
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_requires_python_missing(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when pyproject.toml has no requires-python key."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_requires_python_unparsable(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when requires-python isn't a valid specifier string."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "not a specifier"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_pyproject_malformed(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when pyproject.toml itself isn't valid TOML."""
        (tmp_path / "pyproject.toml").write_text("not valid toml [[[")
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_specifier_excludes_every_known_version(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when the specifier is satisfied by no KNOWN_PYTHON_VERSIONS entry."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "<3.8"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_reads_patch_pinned_lower_bound_on_highest_known_minor(self, tmp_path: Path) -> None:
        """AI: Verify a patch-pinned lower bound on the newest known minor resolves to that minor."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.14.2"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 14)))

    def test_none_when_patch_pin_targets_minor_beyond_known_versions(self, tmp_path: Path) -> None:
        """AI: Verify None is returned when the patch-pinned minor is newer than any KNOWN_PYTHON_VERSIONS entry."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.15.1"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_reads_low_patch_pinned_bound_below_pep_thresholds(self, tmp_path: Path) -> None:
        """AI: Verify a low patch-pinned lower bound combined with an upper bound resolves to the pinned minor."""
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.9.5,<3.10"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 9)))
