from pathlib import Path

from hamcrest import assert_that, is_

from renaissance.utils.python_version import find_nearest_pyproject, minimum_python_version


class TestFindNearestPyproject:
    def test_finds_pyproject_in_same_directory(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        assert_that(find_nearest_pyproject(tmp_path), is_(tmp_path / "pyproject.toml"))

    def test_walks_up_to_parent_pyproject(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        nested = tmp_path / "src" / "pkg"
        nested.mkdir(parents=True)
        assert_that(find_nearest_pyproject(nested), is_(tmp_path / "pyproject.toml"))

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        assert_that(find_nearest_pyproject(tmp_path), is_(None))


class TestMinimumPythonVersion:
    def test_reads_lower_bound_specifier(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.12"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 12)))

    def test_reads_older_lower_bound(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 10)))

    def test_reads_exact_pin(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "==3.14.*"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_((3, 14)))

    def test_none_when_no_pyproject(self, tmp_path: Path) -> None:
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_requires_python_missing(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_requires_python_unparsable(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "not a specifier"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_pyproject_malformed(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("not valid toml [[[")
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))

    def test_none_when_specifier_excludes_every_known_version(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = "<3.8"\n')
        assert_that(minimum_python_version(str(tmp_path / "file.py")), is_(None))
