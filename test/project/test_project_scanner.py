import json

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
    def test_find_sources_raises_not_implemented(self):
        scanner = ProjectScanner()
        assert_that(calling(scanner.find_sources), raises(NotImplementedError))


# ---------------------------------------------------------------------------
# CppScanner
# ---------------------------------------------------------------------------


class TestCppScanner:
    def test_raises_file_not_found_when_compile_commands_missing(self, tmp_path):
        scanner = CppScanner(str(tmp_path / "compile_commands.json"))
        assert_that(calling(scanner.find_sources), raises(FileNotFoundError))

    def test_returns_sorted_unique_files(self, tmp_path):
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
        commands = [{"command": "cc -c foo.cpp"}, {"file": "/src/a.cpp"}]
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps(commands))

        scanner = CppScanner(str(compile_commands))
        result = scanner.find_sources()

        assert_that(result, equal_to(["/src/a.cpp"]))

    def test_returns_empty_list_for_empty_compile_commands(self, tmp_path):
        compile_commands = tmp_path / "compile_commands.json"
        compile_commands.write_text(json.dumps([]))

        scanner = CppScanner(str(compile_commands))
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_default_compile_commands_path(self):
        scanner = CppScanner()
        assert_that(scanner.compile_commands_path, is_("compile_commands.json"))


# ---------------------------------------------------------------------------
# JavaScanner
# ---------------------------------------------------------------------------


class TestJavaScanner:
    def test_finds_java_files_recursively(self, tmp_path):
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
        (tmp_path / "B.java").write_text("")
        (tmp_path / "A.java").write_text("")

        scanner = JavaScanner(str(tmp_path))
        result = scanner.find_sources()

        assert_that(result, equal_to(sorted(result)))

    def test_returns_empty_list_when_no_java_files(self, tmp_path):
        scanner = JavaScanner(str(tmp_path))
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_default_root_dir(self):
        scanner = JavaScanner()
        assert_that(scanner.root_dir, is_("."))


# ---------------------------------------------------------------------------
# PythonScanner
# ---------------------------------------------------------------------------


class TestPythonScanner:
    def test_finds_python_files_in_package_dirs(self, tmp_path):
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
        scanner = PythonScanner(str(tmp_path), package_dirs=["nonexistent"])
        result = scanner.find_sources()

        assert_that(result, is_(empty()))

    def test_returns_sorted_results(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "z_module.py").write_text("")
        (src / "a_module.py").write_text("")

        scanner = PythonScanner(str(tmp_path), package_dirs=["src"])
        result = scanner.find_sources()

        assert_that(result, equal_to(sorted(result)))

    def test_searches_multiple_package_dirs(self, tmp_path):
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
        scanner = PythonScanner()
        assert_that(scanner.package_dirs, equal_to(["src", "lib", "test"]))

    def test_default_root_dir(self):
        scanner = PythonScanner()
        assert_that(scanner.root_dir, is_("."))


# ---------------------------------------------------------------------------
# BearCppScanner
# ---------------------------------------------------------------------------


class TestBearCppScanner:
    def test_find_sources_calls_run_bear_when_compile_commands_missing(self, tmp_path, mocker):
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
        scanner = BearCppScanner()
        mocker.patch("renaissance.project.project_scanner.system", return_value=1)

        assert_that(calling(scanner.run_bear), raises(RuntimeError))

    def test_run_bear_succeeds_on_zero_exit(self, mocker):
        scanner = BearCppScanner()
        mocker.patch("renaissance.project.project_scanner.system", return_value=0)

        # Should not raise
        scanner.run_bear()

    def test_default_build_dir(self):
        scanner = BearCppScanner()
        assert_that(scanner.build_dir, is_("."))
