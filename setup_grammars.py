import subprocess
import sys

# Languages you want to install
language_packages = [
    "tree-sitter-languages",
    "tree-sitter-python",
    "tree-sitter-cpp",
    "tree-sitter-java",
]


def install(package):
    print(f"📦 Installing {package}...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", package])
    if result.returncode != 0:
        print(f"❌ Failed to install: {package}")
    else:
        print(f"✅ Installed: {package}")


if __name__ == "__main__":
    for pkg in language_packages:
        install(pkg)
