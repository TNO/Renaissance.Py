"""Language-specific source file scanners used to feed recipes with the files to process."""

import json
import subprocess
from pathlib import Path


class ProjectScanner:
    """Base class for language-specific source file scanners."""

    def find_sources(self) -> list[str]:
        """Return the paths of source files found by this scanner. Implemented by subclasses."""
        raise NotImplementedError


class CppScanner(ProjectScanner):
    """Scan a C/C++ project's compile_commands.json for source files."""

    def __init__(self, compile_commands_path: str = "compile_commands.json") -> None:
        """Store the path to the compile_commands.json to read sources from."""
        self.compile_commands_path = compile_commands_path

    def find_sources(self) -> list[str]:
        """Return every file entry listed in compile_commands.json, sorted and deduplicated."""
        if not Path(self.compile_commands_path).exists():
            message = "compile_commands.json not found"
            raise FileNotFoundError(message)
        with Path(self.compile_commands_path).open() as f:
            commands = json.load(f)
        return sorted({entry["file"] for entry in commands if "file" in entry})


class JavaScanner(ProjectScanner):
    """Scan a directory tree for Java source files."""

    def __init__(self, root_dir: str = ".") -> None:
        """Store the root directory to scan for .java files."""
        self.root_dir = root_dir

    def find_sources(self) -> list[str]:
        """Return every .java file under root_dir, sorted."""
        # TODO: is this correct? does this filter out files correctly?
        # See https://github.com/TNO/Renaissance.Py/issues/200

        java_files = Path(self.root_dir).rglob("*.java")
        return sorted(str(f) for f in java_files)


class PythonScanner(ProjectScanner):
    """Scan a directory tree for Python source files."""

    EXCLUDED_DIRS = frozenset({".git", "__pycache__", ".venv", "venv"})
    # TODO: incomplete list, extend this list with more files/directories that should always be ignored

    def __init__(self, root_dir: str = ".", package_dirs: list[str] | None = None) -> None:
        """Store the scan root and optional package_dirs narrowing.

        package_dirs, when given, narrows the scan to those subdirectories of root_dir.
        Left as None (the default), the whole of root_dir is scanned instead of assuming a
        src/lib/test layout, since that assumption silently skipped real third-party layouts.
        """
        self.root_dir = root_dir
        self.package_dirs = package_dirs

    def find_sources(self) -> list[Path]:
        """Return every .py file under root_dir (or package_dirs, if given), sorted, excluding EXCLUDED_DIRS."""
        roots = [Path(self.root_dir) / d for d in self.package_dirs] if self.package_dirs else [Path(self.root_dir)]
        files = []
        for root in roots:
            if not root.exists():
                continue
            files.extend(path for path in root.rglob("*.py") if not any(part in self.EXCLUDED_DIRS for part in path.parts))
        return sorted(files)


class BearCppScanner(CppScanner):
    """CppScanner that generates compile_commands.json via Bear when it's missing."""

    def __init__(self, build_dir: str = ".", compile_commands_path: str = "compile_commands.json") -> None:
        """Store the build directory to run Bear in, alongside the compile_commands.json path."""
        super().__init__(compile_commands_path)
        self.build_dir = build_dir

    def run_bear(self) -> None:
        """Run Bear to generate compile_commands.json by wrapping the project's make invocation."""
        # bear is resolved via PATH intentionally; build_dir isn't attacker-controlled here.
        result = subprocess.run(["bear", "--", "make", "-C", self.build_dir], check=False)  # noqa: S603, S607
        if result.returncode != 0:
            message = "Bear failed to run or make failed."
            raise RuntimeError(message)

    def find_sources(self) -> list[str]:
        """Generate compile_commands.json via Bear if missing, then return its listed sources."""
        if not Path(self.compile_commands_path).exists():
            self.run_bear()
        return super().find_sources()
