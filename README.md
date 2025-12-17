# LST Toolkit

This toolkit provides a parser-independent Language-Specific Tree (LST) representation with pattern matching, symbol binding, and extraction capabilities. It supports Tree-sitter grammars and offers a flexible interface for analyzing Python, Java, and C++ code.

---

## 📦 Features

- Generic internal AST representation (`LSTNode`)
- Structural pattern matching with placeholders
- Node-type based matchers
- Match abstraction layer (`Match`)
- Rule-based extractor (templated, with filtering)
- Symbol table for declarations, definitions, and uses
- Extensible for multi-language support
- Includes examples for Python, Java, and C++
- Unit-tested matcher components
- VSCode integration

---

## 🔧 Installation

1. Clone or unzip the project.
2. Install dependencies:

```bash
pip install -e .
```

```bash
pip install tree-sitter
```
with a dash and not an underscore

3. Run the setup script to clone grammars and build the shared library:

```bash
python setup_grammars.py
```

This will:
- Clone Tree-sitter grammars for Python, Java, and C++
- Build `build/my-languages.so` for use in adapters

---

## 🧪 Running Tests

```bash
python -m unittest discover tests
```

---

## 🧰 Examples

Python:

```bash
python examples/python_example.py
```

Java:

```bash
cat examples/java_example.java
```

C++:

```bash
cat examples/cpp_example.cpp
```

---

## 🧠 Structure

- `core/lst.py` — Internal node structure
- `core/tree_sitter_adapter.py` — Parser adapter
- `core/pattern_matcher.py` — Structural matcher
- `core/node_type_matcher.py` — Node-type matcher
- `core/match.py` — Match abstraction
- `core/extractor.py` — Rule-based extractor
- `core/symbols.py` — Symbol table
- `examples/` — Example input files
- `tests/` — Unit tests
- `setup_grammars.py` — Auto-installs Tree-sitter grammars

---

## 🧩 Integration

You can use `Extractor`, `Match`, and `PatternMatcherInterfaceExtended` to write custom rules.

Example:

```python
extractor = Extractor(interface)
extractor.add_rule("function_definition", lambda m: m.first("match").signature)
results = extractor.run(source_code)
```

---

## 🚀 License

MIT License — feel free to use and extend.


## 🔌 Clang Integration for C++

For advanced C++ analysis (with preprocessing and include resolution), this toolkit supports [libclang](https://clang.llvm.org/).

### 🛠 Install Dependencies

```bash
# On Ubuntu/Debian
sudo apt install libclang-dev

# Python bindings
pip install clang
```

### 🔧 Usage

Use `ClangAdapter` instead of `TreeSitterAdapter`:

```python
from core.clang_adapter import ClangAdapter

adapter = ClangAdapter()
lst = adapter.parse("examples/cpp_example.cpp")

for node in lst.traverse():
    print(node)
```

The `ClangAdapter` provides:
- Full include resolution
- Macro expansion
- AST node types like `FUNCTION_DECL`, `CALL_EXPR`, etc.
- Source location metadata
