# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests that dropping `covariant=`/`contravariant=` is safe for functions and unsafe for classes.

The type checker (pyright) and the interpreter judge the code before and after TypeParameterCheck.convert_declared_typevars.
"""

import importlib.util
import json
import subprocess
import sys
from typing import TYPE_CHECKING, NamedTuple

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_item, has_property, not_

from renaissance.recipes.type_parameter_rules import UnsafeReason

# TODO(FrancescoPezzella): Replace with a lazy import in Python 3.15.
#  https://github.com/TNO/Renaissance.Py/issues/275
if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

    from renaissance.recipes.type_parameter_check import TypeParameterCheck


class _Diagnostic(NamedTuple):
    """One pyright finding, without the file it was found in."""

    line: int
    severity: str
    rule: str
    message: str


def _write(source: str, path: Path) -> Path:
    """Write `source` to `path` and return `path`."""
    path.write_text(source, encoding="utf-8")
    return path


def _type_check(path: Path) -> list[_Diagnostic]:
    """Return every diagnostic pyright reports for the file at `path`, `reveal_type` results included."""
    command = [sys.executable, "-m", "pyright", "--pythonpath", sys.executable, "--outputjson", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", cwd=path.parent, check=False)  # noqa: S603 - fixed argv
    report = json.loads(result.stdout[result.stdout.index("{") :])
    return [
        _Diagnostic(item["range"]["start"]["line"] + 1, item["severity"], item.get("rule", ""), item["message"])
        for item in report["generalDiagnostics"]
    ]


def _import(path: Path) -> ModuleType:
    """Import the file at `path` as a module."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        message = f"could not load {path}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FUNCTION_TEMPLATE = """\
from collections.abc import Callable
from typing import TypeVar, reveal_type

{declaration}


def first(x: T) -> T:
    return x


reveal_type(first(1))
reveal_type(first("a"))
reveal_type(first([1]))
accepted: Callable[[bool], int] = first
rejected: Callable[[int], str] = first
"""

_PROTOCOL = """\
class Reader(Protocol[T_co]):
    def read(self) -> T_co: ...
"""

_GENERIC_CLASS = """\
class Reader(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self._value = value

    def read(self) -> T_co:
        return self._value
"""

_CLASS_TEMPLATE = """\
from typing import Generic, Protocol, TypeVar, reveal_type

T_co = TypeVar("T_co"{covariant})


{class_definition}

def read_twice(reader: Reader[T_co]) -> tuple[T_co, T_co]:
    return reader.read(), reader.read()


def widen(reader: Reader[int]) -> None:
    wider: Reader[object] = reader
    reveal_type(wider)
"""


class TestVarianceOfFunctions:
    """A function's TypeVar has no variance, so dropping it must not change anything."""

    @pytest.mark.parametrize(
        "declaration",
        [
            pytest.param('T = TypeVar("T", covariant=True)', id="covariant"),
            pytest.param('T = TypeVar("T", contravariant=True)', id="contravariant"),
            pytest.param('T = TypeVar("T", bound=int, covariant=True)', id="bound-and-covariant"),
        ],
    )
    def test_function_behaves_the_same_without_the_variance(
        self,
        create_type_parameter_check: Callable[[str], TypeParameterCheck],
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Verify the type checker accepts, rejects and infers exactly as before, and the function returns the same values."""
        before = _FUNCTION_TEMPLATE.format(declaration=declaration)
        subject = create_type_parameter_check(before)

        result = subject.convert_declared_typevars()

        after = subject.apply_to_string()
        assert_that(result, equal_to({"T": "fixed"}))
        assert_that(after, contains_string("def first[T"))
        before_path = _write(before, tmp_path / "before.py")
        after_path = _write(after, tmp_path / "after.py")
        before_findings = _type_check(before_path)
        assert_that(before_findings, has_item(has_property("message", contains_string('Type of "first(1)" is "int"'))))
        assert_that(before_findings, has_item(has_property("rule", "reportAssignmentType")))
        assert_that(_type_check(after_path), equal_to(before_findings))
        values = (1, "a", [1])
        assert_that(
            [_import(after_path).first(value) for value in values],
            equal_to([_import(before_path).first(value) for value in values]),
        )


class TestVarianceOfClasses:
    """A generic class's variance changes what the type checker accepts, so only functions may lose it."""

    @pytest.mark.parametrize(
        ("class_definition", "class_header"),
        [
            pytest.param(_PROTOCOL, "class Reader(Protocol[T_co]):", id="protocol"),
            pytest.param(_GENERIC_CLASS, "class Reader(Generic[T_co]):", id="generic-class"),
        ],
    )
    def test_class_keeps_its_variance_and_dropping_it_changes_the_type_checking(
        self,
        create_type_parameter_check: Callable[[str], TypeParameterCheck],
        tmp_path: Path,
        class_definition: str,
        class_header: str,
    ) -> None:
        """Verify the class and its covariant declaration stay, the code still type checks, and dropping the variance does not."""
        covariant = _CLASS_TEMPLATE.format(covariant=", covariant=True", class_definition=class_definition)
        subject = create_type_parameter_check(covariant)

        result = subject.convert_declared_typevars()

        converted = subject.apply_to_string()
        assert_that(result, equal_to({"T_co": "fixed"}))
        assert_that(subject.converted_unsafe_reasons, equal_to({"T_co": UnsafeReason.USED_IN_GENERIC_CLASS}))
        assert_that(converted, contains_string("def read_twice[T_co](reader: Reader[T_co])"))
        assert_that(converted, contains_string('T_co = TypeVar("T_co", covariant=True)'))
        assert_that(converted, contains_string(class_header))
        original_findings = _type_check(_write(covariant, tmp_path / "original.py"))
        assert_that(original_findings, has_item(has_property("message", contains_string('Type of "wider" is "Reader[int]"'))))
        assert_that(_type_check(_write(converted, tmp_path / "converted.py")), equal_to(original_findings))
        assert_that([finding.rule for finding in original_findings], not_(has_item("reportAssignmentType")))

        invariant = converted.replace(", covariant=True", "")
        invariant_rules = [finding.rule for finding in _type_check(_write(invariant, tmp_path / "invariant.py"))]
        assert_that(invariant_rules, has_item("reportAssignmentType"))
