import os
import subprocess
from tree_sitter import Language

GRAMMARS = {
    "python": "https://github.com/tree-sitter/tree-sitter-python",
    "java": "https://github.com/tree-sitter/tree-sitter-java",
    "cpp": "https://github.com/tree-sitter/tree-sitter-cpp",
}

GRAMMAR_DIR = "tree-sitter-grammars"
BUILD_OUTPUT = "build/my-languages.so"


def clone_grammars():
    os.makedirs(GRAMMAR_DIR, exist_ok=True)
    for name, url in GRAMMARS.items():
        target = os.path.join(GRAMMAR_DIR, f"tree-sitter-{name}")
        if not os.path.exists(target):
            print(f"Cloning {name}...")
            subprocess.run(["git", "clone", url, target], check=True)
        else:
            print(f"{name} already cloned.")


def build_library():
    paths = [os.path.join(GRAMMAR_DIR, f"tree-sitter-{name}") for name in GRAMMARS]
    os.makedirs("build", exist_ok=True)
    print("Building shared language library...")
    Language.build_library(BUILD_OUTPUT, paths)
    print(f"Library written to: {BUILD_OUTPUT}")


if __name__ == "__main__":
    clone_grammars()
    # build_library()
