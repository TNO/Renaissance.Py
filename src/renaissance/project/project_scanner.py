import json
import subprocess
from pathlib import Path


class ProjectScanner:
    def find_sources(self) -> list[str]:
        raise NotImplementedError


class CppScanner(ProjectScanner):
    def __init__(self, compile_commands_path: str = "compile_commands.json"):
        self.compile_commands_path = compile_commands_path

    def find_sources(self) -> list[str]:
        if not Path(self.compile_commands_path).exists():
            raise FileNotFoundError("compile_commands.json not found")
        with Path(self.compile_commands_path).open() as f:
            commands = json.load(f)
        return sorted(set(entry["file"] for entry in commands if "file" in entry))


class JavaScanner(ProjectScanner):
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir

    def find_sources(self) -> list[str]:
        # TODO: is this correct? does this filter out files correctly?
        java_files = Path(self.root_dir).rglob("*.java")
        return sorted(str(f) for f in java_files)


class PythonScanner(ProjectScanner):
    EXCLUDED_DIRS = frozenset({".git", "__pycache__", ".venv", "venv"})
    # TODO: incomplete list, extend this list with more files/directories that should always be ignored

    def __init__(self, root_dir: str = ".", package_dirs: list[str] | None = None):
        """package_dirs, when given, narrows the scan to those subdirectories of root_dir.
        Left as None (the default), the whole of root_dir is scanned
        """
        self.root_dir = root_dir
        self.package_dirs = package_dirs

    def find_sources(self) -> list[Path]:
        roots = [Path(self.root_dir) / d for d in self.package_dirs] if self.package_dirs else [Path(self.root_dir)]
        files = []
        for root in roots:
            if not root.exists():
                continue
            files.extend(path for path in root.rglob("*.py") if not any(part in self.EXCLUDED_DIRS for part in path.parts))
        return sorted(files)


class BearCppScanner(CppScanner):
    def __init__(self, build_dir: str = ".", compile_commands_path: str = "compile_commands.json"):
        super().__init__(compile_commands_path)
        self.build_dir = build_dir

    def run_bear(self):
        print("Running Bear to generate compile_commands.json...")
        result = subprocess.run(["bear", "--", "make", "-C", self.build_dir])
        if result.returncode != 0:
            raise RuntimeError("Bear failed to run or make failed.")

    def find_sources(self) -> list[str]:
        if not Path(self.compile_commands_path).exists():
            self.run_bear()
        return super().find_sources()
