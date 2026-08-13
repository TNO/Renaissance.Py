import sys
from pathlib import Path

from rejuvenation import cli


def test_refactor_file_argument_processes_single_file(tmp_path, mocker, monkeypatch):
    target_file = tmp_path / "sample_test.py"
    target_file.write_text("x = 1\n", encoding="utf-8")

    process = mocker.patch("rejuvenation.cli.PythonRefactoring.process")
    monkeypatch.setattr(sys, "argv", ["rejuvenate", "refactor", "Taut2Pyunit", str(target_file)])

    cli.refactor()

    process.assert_called_once_with("Taut2Pyunit", target_file)


def test_refactor_directory_argument_recurses(tmp_path, mocker, monkeypatch):
    target_dir = tmp_path / "suite"
    nested_dir = target_dir / "nested"
    nested_dir.mkdir(parents=True)

    top_level_py = target_dir / "top_level_test.py"
    nested_py = nested_dir / "nested_test.py"
    ignored_txt = nested_dir / "README.txt"
    top_level_py.write_text("x = 1\n", encoding="utf-8")
    nested_py.write_text("y = 2\n", encoding="utf-8")
    ignored_txt.write_text("ignore\n", encoding="utf-8")

    process = mocker.patch("rejuvenation.cli.PythonRefactoring.process")
    monkeypatch.setattr(sys, "argv", ["rejuvenate", "refactor", "Taut2Pyunit", str(target_dir)])

    cli.refactor()

    called_files = {Path(call.args[1]).resolve() for call in process.call_args_list}
    assert called_files == {top_level_py.resolve(), nested_py.resolve()}


def test_refactor_directory_argument_supports_dot(tmp_path, mocker, monkeypatch):
    nested_dir = tmp_path / "tests"
    nested_dir.mkdir(parents=True)

    root_py = tmp_path / "root_test.py"
    nested_py = nested_dir / "nested_test.py"
    root_py.write_text("x = 1\n", encoding="utf-8")
    nested_py.write_text("y = 2\n", encoding="utf-8")

    process = mocker.patch("rejuvenation.cli.PythonRefactoring.process")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["rejuvenate", "refactor", "Taut2Pyunit", "."])

    cli.refactor()

    called_files = {Path(call.args[1]).resolve() for call in process.call_args_list}
    assert called_files == {root_py.resolve(), nested_py.resolve()}
