"""AI: Scanners that discover project source files from a compilation database or file system."""

import json
from os import system
from pathlib import Path


class ProjectScanner:
    """AI: Base scanner interface for discovering a project's source files."""

    def find_sources(self) -> list[str]:
        """AI: Discover and return this project's source file paths."""
        raise NotImplementedError


class CppScanner(ProjectScanner):
    """AI: Scanner that discovers C/C++ sources from a compilation database."""

    def __init__(self, compile_commands_path: str = "compile_commands.json"):
        """AI: Configure a scanner that discovers C/C++ sources from a compilation database."""
        self.compile_commands_path = compile_commands_path

    def find_sources(self) -> list[str]:
        """AI: Discover C/C++ source files listed in the compilation database."""
        if not Path(self.compile_commands_path).exists():
            raise FileNotFoundError("compile_commands.json not found")
        with Path(self.compile_commands_path).open() as f:
            commands = json.load(f)
        return sorted(set(entry["file"] for entry in commands if "file" in entry))


class JavaScanner(ProjectScanner):
    """AI: Scanner that discovers Java sources under a root directory."""

    def __init__(self, root_dir: str = "."):
        """AI: Configure a scanner that discovers Java sources under a root directory."""
        self.root_dir = root_dir

    def find_sources(self) -> list[str]:
        """AI: Discover Java source files recursively under the root directory."""
        java_files = Path(self.root_dir).rglob("*.java")
        return sorted(str(f) for f in java_files)


class PythonScanner(ProjectScanner):
    """AI: Scanner that discovers Python sources under known package directories."""

    def __init__(self, root_dir: str = ".", package_dirs: list[str] | None = None):
        """AI: Configure a scanner that discovers Python sources under known package directories."""
        # return (file_path for file_path in current_dir.iterdir() if is_python_file)

        self.root_dir = root_dir
        self.package_dirs = package_dirs or ["src", "lib", "test"]
        # TODO: Why this hardcoded default heuristic?
        #       Why not what Python by default enforces or what is derived from the project config?

    def find_sources(self) -> list[str]:
        """AI: Discover Python source files under each configured package directory."""
        files = []

        for d in self.package_dirs:
            file_path = Path(self.root_dir) / d
            if file_path.exists():
                files.extend(file_path.glob("**/*.py"))
        return sorted(files)


class BearCppScanner(CppScanner):
    """AI: Scanner that generates a compilation database via Bear before discovering sources."""

    def __init__(self, build_dir: str = ".", compile_commands_path: str = "compile_commands.json"):
        """AI: Configure a scanner that generates a compilation database via Bear before discovering sources."""
        super().__init__(compile_commands_path)
        self.build_dir = build_dir

    def run_bear(self):
        """AI: Regenerate the compilation database by running Bear over the configured build."""
        print("Running Bear to generate compile_commands.json...")
        result = system(f"bear -- make -C {self.build_dir}")
        if result != 0:
            raise RuntimeError("Bear failed to run or make failed.")

    def find_sources(self) -> list[str]:
        """AI: Generate the compilation database via Bear if missing, then discover C/C++ sources from it."""
        if not Path(self.compile_commands_path).exists():
            self.run_bear()
        return super().find_sources()
