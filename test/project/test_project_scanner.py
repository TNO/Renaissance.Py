"""Tests for the project source-file scanners."""

import json
from unittest.mock import Mock

import pytest
from hamcrest import assert_that, calling, contains_inanyorder, empty, equal_to, is_, raises

from renaissance.project.project_scanner import (
    BearCppScanner,
    CppScanner,
    JavaScanner,
    ProjectScanner,
    PythonScanner,
)

# ---------------------------------------------------------------------------
# ProjectScanner (base)
# ---------------------------------------------------------------------------


class TestProjectScanner:
    """AI: Tests the base ProjectScanner raises NotImplementedError."""

    def test_find_sources_raises_not_implemented(self):
        """AI: Assert the base ProjectScanner.find_sources raises NotImplementedError."""
        scanner = ProjectScanner()
        assert_that(calling(scanner.find_sources), raises(NotImplementedError))


# ---------------------------------------------------------------------------
# CppScanner
# ---------------------------------------------------------------------------


class TestCppScanner:
    """AI: Tests discovering C/C++ sources from a compilation database via CppScanner."""

    def test_raises_file_not_found_when_compile_commands_missing(self, tmp_path):
        """AI: Assert CppScanner.find_sources raises FileNotFoundError when the compile database is missing."""
        scanner = CppScanner(str(tmp_path / "compile_commands.json"))
        assert_that(calling(scanner.find_sources), raises(FileNotFoundError))

    def test_returns_sorted_unique_files(self, tmp_path):
        """AI: Assert CppScanner.find_sources returns sorted, de-duplicated file paths from the compile database."""
        commands = [
            {"file": "/src/b.cpp"},
            {"file": "/src/a.cpp"},
            {"file": "/src/b.cpp"},
        ]
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps(commands))

        scanner = CppScanner(str(compile_commands))
        result = scanner.find_sources()

        assert_that(result, equal_to(["/src/a.cpp", "/src/b.cpp"]))

    def test_ignores_entries_without_file_key(self, tmp_path):
        """AI: Assert CppScanner.find_sources skips compile-database entries lacking a "file" key."""
        commands = [{"command": "cc -c foo.cpp"}, {"file": "/src/a.cpp"}]
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps(commands))

        scanner = CppScanner(str(compile_commands))
        result = scanner.find_sources()

        assert_that(result, equal_to(["/src/a.cpp"]))

    def test_returns_empty_list_for_empty_compile_commands(self, tmp_path):
        """AI: Assert CppScanner.find_sources returns an empty list for an empty compile database."""
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps([]))

        scanner = CppScanner(str(compile_commands))
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_default_compile_commands_path(self):
        """AI: Assert CppScanner defaults compile_commands_path to "compile_commands.json"."""
        scanner = CppScanner()
        assert_that(scanner.compile_commands_path, is_("compile_commands.json"))


# ---------------------------------------------------------------------------
# JavaScanner
# ---------------------------------------------------------------------------


class TestJavaScanner:
    """AI: Tests discovering Java sources under a root directory via JavaScanner."""

    def test_finds_java_files_recursively(self, tmp_path):
        """AI: Assert JavaScanner.find_sources recursively discovers .java files under nested directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "Main.java").write_text("class Main {}")
        (tmp_path / "src" / "sub").mkdir()
        (tmp_path / "src" / "sub" / "Util.java").write_text("class Util {}")

        scanner = JavaScanner(str(tmp_path))
        result = scanner.find_sources()

        assert_that(
            result,
            contains_inanyorder(
                str(tmp_path / "src" / "Main.java"),
                str(tmp_path / "src" / "sub" / "Util.java"),
            ),
        )

    def test_returns_sorted_results(self, tmp_path):
        """AI: Assert JavaScanner.find_sources returns results in sorted order."""
        (tmp_path / "B.java").write_text("")
        (tmp_path / "A.java").write_text("")

        scanner = JavaScanner(str(tmp_path))
        result = scanner.find_sources()

        assert_that(result, equal_to(sorted(result)))

    def test_returns_empty_list_when_no_java_files(self, tmp_path):
        """AI: Assert JavaScanner.find_sources returns an empty list when no .java files exist."""
        scanner = JavaScanner(str(tmp_path))
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_default_root_dir(self):
        """AI: Assert JavaScanner defaults root_dir to "."."""
        scanner = JavaScanner()
        assert_that(scanner.root_dir, is_("."))


# ---------------------------------------------------------------------------
# PythonScanner
# ---------------------------------------------------------------------------


class TestPythonScanner:
    """AI: Tests discovering Python sources under known package directories via PythonScanner."""

    def test_finds_python_files_in_package_dirs(self, tmp_path):
        """AI: Assert PythonScanner.find_sources discovers .py files under configured package directories."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text("")
        (src / "sub").mkdir()
        (src / "sub" / "helper.py").write_text("")

        scanner = PythonScanner(str(tmp_path), package_dirs=["src"])
        result = scanner.find_sources()

        assert_that(
            [str(p) for p in result],
            contains_inanyorder(
                str(src / "module.py"),
                str(src / "sub" / "helper.py"),
            ),
        )

    def test_skips_nonexistent_package_dirs(self, tmp_path):
        """AI: Assert PythonScanner.find_sources skips package directories that don't exist."""
        scanner = PythonScanner(str(tmp_path), package_dirs=["nonexistent"])
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_returns_sorted_results(self, tmp_path):
        """AI: Assert PythonScanner.find_sources returns results in sorted order."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "z_module.py").write_text("")
        (src / "a_module.py").write_text("")

        scanner = PythonScanner(str(tmp_path), package_dirs=["src"])
        result = scanner.find_sources()

        assert_that(result, equal_to(sorted(result)))

    def test_searches_multiple_package_dirs(self, tmp_path):
        """AI: Assert PythonScanner.find_sources searches across all configured package directories."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("")
        (tmp_path / "lib").mkdir()
        (tmp_path / "lib" / "b.py").write_text("")

        scanner = PythonScanner(str(tmp_path), package_dirs=["src", "lib"])
        result = [str(p) for p in scanner.find_sources()]

        assert_that(
            result,
            contains_inanyorder(
                str(tmp_path / "src" / "a.py"),
                str(tmp_path / "lib" / "b.py"),
            ),
        )

    def test_default_package_dirs(self):
        """AI: Assert PythonScanner defaults package_dirs to ["src", "lib", "test"]."""
        scanner = PythonScanner()
        assert_that(scanner.package_dirs, is_(None))

    def test_default_root_dir(self):
        """AI: Assert PythonScanner defaults root_dir to "."."""
        scanner = PythonScanner()
        assert_that(scanner.root_dir, is_("."))

    @pytest.mark.parametrize("excluded_dir", sorted(PythonScanner.EXCLUDED_DIRS))
    def test_excludes_known_noise_dirs_in_default_whole_tree_scan(self, tmp_path, excluded_dir):
        noise_dir = tmp_path / excluded_dir
        noise_dir.mkdir()
        (noise_dir / "ignored.py").write_text("")
        (tmp_path / "kept.py").write_text("")

        scanner = PythonScanner(str(tmp_path))
        result = [p.name for p in scanner.find_sources()]

        assert_that(result, equal_to(["kept.py"]))

    @pytest.mark.parametrize("excluded_dir", sorted(PythonScanner.EXCLUDED_DIRS))
    def test_excludes_known_noise_dirs_within_explicit_package_dirs(self, tmp_path, excluded_dir):
        src = tmp_path / "src"
        src.mkdir()
        noise_dir = src / excluded_dir
        noise_dir.mkdir()
        (noise_dir / "ignored.py").write_text("")
        (src / "kept.py").write_text("")

        scanner = PythonScanner(str(tmp_path), package_dirs=["src"])
        result = [p.name for p in scanner.find_sources()]

        assert_that(result, equal_to(["kept.py"]))

    def test_default_package_dirs_scans_whole_root_dir(self, tmp_path):
        # Motivating case: source living outside src/lib/test (e.g. redis-py's redis/ layout).
        redis_like = tmp_path / "redis"
        redis_like.mkdir()
        (redis_like / "client.py").write_text("")

        scanner = PythonScanner(str(tmp_path))
        result = [str(p) for p in scanner.find_sources()]

        assert_that(result, equal_to([str(redis_like / "client.py")]))


# ---------------------------------------------------------------------------
# BearCppScanner
# ---------------------------------------------------------------------------


class TestBearCppScanner:
    """AI: Tests generating a compilation database via Bear before discovering sources."""

    def test_find_sources_calls_run_bear_when_compile_commands_missing(self, tmp_path, mocker):
        """AI: Assert BearCppScanner.find_sources runs Bear when the compile database is missing."""
        scanner = BearCppScanner(
            build_dir=str(tmp_path),
            compile_commands_path=str(tmp_path / "compile_commands.json"),
        )
        mock_bear = mocker.patch.object(scanner, "run_bear")

        # After run_bear is called the file still won't exist, so super().find_sources()
        # will raise FileNotFoundError — that's acceptable; we only care that run_bear ran.
        with pytest.raises(FileNotFoundError):
            scanner.find_sources()

        assert_that(mock_bear.call_count, is_(1))

    def test_find_sources_does_not_call_run_bear_when_compile_commands_exists(self, tmp_path, mocker):
        """AI: Assert BearCppScanner.find_sources skips running Bear when the compile database already exists."""
        commands = [{"file": "/src/main.cpp"}]
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps(commands))

        scanner = BearCppScanner(
            build_dir=str(tmp_path),
            compile_commands_path=str(compile_commands),
        )
        mock_bear = mocker.patch.object(scanner, "run_bear")

        result = scanner.find_sources()

        mock_bear.assert_not_called()
        assert_that(result, equal_to(["/src/main.cpp"]))

    def test_run_bear_raises_on_nonzero_exit(self, mocker):
        """AI: Assert BearCppScanner.run_bear raises RuntimeError when the Bear subprocess exits non-zero."""
        scanner = BearCppScanner()
        mocker.patch("renaissance.project.project_scanner.subprocess.run", return_value=Mock(returncode=1))

        assert_that(calling(scanner.run_bear), raises(RuntimeError))

    def test_run_bear_succeeds_on_zero_exit(self, mocker):
        """AI: Assert BearCppScanner.run_bear does not raise when the Bear subprocess exits zero."""
        scanner = BearCppScanner()
        mocker.patch("renaissance.project.project_scanner.subprocess.run", return_value=Mock(returncode=0))

        # Should not raise
        scanner.run_bear()

    def test_default_build_dir(self):
        """AI: Assert BearCppScanner defaults build_dir to "."."""
        scanner = BearCppScanner()
        assert_that(scanner.build_dir, is_("."))
