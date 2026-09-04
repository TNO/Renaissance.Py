import json
from os import path, system
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
        java_files = Path(self.root_dir).rglob("*.java")
        return sorted(str(f) for f in java_files)


class PythonScanner(ProjectScanner):
    def __init__(self, root_dir: str = ".", package_dirs: list[str] | None = None):

        # return (file_path for file_path in current_dir.iterdir() if is_python_file)

        self.root_dir = root_dir
        self.package_dirs = package_dirs or ["src", "lib", "test"]
        # TODO: Why this hardcoded default heuristic?
        #       Why not what Python by default enforces or what is derived from the project config?

    def find_sources(self) -> list[str]:
        files = []

        for d in self.package_dirs:
            file_path = Path(self.root_dir) / d
            if file_path.exists():
                files.extend(file_path.glob("**/*.py"))
        return sorted(files)


class BearCppScanner(CppScanner):
    def __init__(self, build_dir: str = ".", compile_commands_path: str = "compile_commands.json"):
        super().__init__(compile_commands_path)
        self.build_dir = build_dir

    def run_bear(self):
        print("Running Bear to generate compile_commands.json...")
        result = system(f"bear -- make -C {self.build_dir}")
        if result != 0:
            raise RuntimeError("Bear failed to run or make failed.")

    def find_sources(self) -> list[str]:
        if not Path(self.compile_commands_path).exists():
            self.run_bear()
        return super().find_sources()
