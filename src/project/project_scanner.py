import os
import json
import glob
import xml.etree.ElementTree as ET
from typing import List
from pathlib import Path


class ProjectScanner:
    def find_sources(self) -> List[str]:
        raise NotImplementedError


class CppScanner(ProjectScanner):
    def __init__(self, compile_commands_path: str = "compile_commands.json"):
        self.compile_commands_path = compile_commands_path

    def find_sources(self) -> List[str]:
        if not os.path.exists(self.compile_commands_path):
            raise FileNotFoundError("compile_commands.json not found")
        with open(self.compile_commands_path) as f:
            commands = json.load(f)
        return sorted(set(entry["file"] for entry in commands if "file" in entry))


class JavaScanner(ProjectScanner):
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir

    def find_sources(self) -> List[str]:
        java_files = glob.glob(f"{self.root_dir}/**/*.java", recursive=True)
        return sorted(java_files)


class PythonScanner(ProjectScanner):
    def __init__(self, root_dir: str = ".", package_dirs: List[str] = None):
        self.root_dir = root_dir
        self.package_dirs = package_dirs or ["src", "lib", ""]

    def find_sources(self) -> List[str]:
        files = []
        for d in self.package_dirs:
            path = Path(self.root_dir) / d
            if path.exists():
                files.extend(str(p) for p in path.rglob("*.py") if p.is_file())
        return sorted(files)


class BearCppScanner(CppScanner):
    def __init__(self, build_dir: str = ".", compile_commands_path: str = "compile_commands.json"):
        super().__init__(compile_commands_path)
        self.build_dir = build_dir

    def run_bear(self):
        print("Running Bear to generate compile_commands.json...")
        result = os.system(f"bear -- make -C {self.build_dir}")
        if result != 0:
            raise RuntimeError("Bear failed to run or make failed.")

    def find_sources(self) -> List[str]:
        if not os.path.exists(self.compile_commands_path):
            self.run_bear()
        return super().find_sources()
