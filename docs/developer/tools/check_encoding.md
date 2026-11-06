<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Encoding check

`tools/check_encoding.py` fails the build when a file in the repository is not UTF-8, or is UTF-8 but starts with a byte order mark.

## The rule it enforces

Every text file in the repository is encoded as UTF-8, without a byte order mark. This covers everything `git` tracks: Python
sources, Markdown pages, feature files, YAML workflows, JSON and TOML configuration, and the C, C++, Java and Go files used as
test input.

One encoding for the whole repository keeps the sources readable on every platform. Windows still decodes with the ANSI code page
by default, so a file saved as Latin-1 or UTF-16 silently becomes mojibake: `ruff`, `pyright`, `mkdocs` or a parser test fails on
a character nobody typed, and the first person who saves the file again produces a diff full of unrelated changes.

A byte order mark is rejected for a separate reason. It is valid UTF-8, but `encoding="utf-8"` does not strip it, so it survives
as a U+FEFF character at the start of the first token — in a shebang, in a YAML document marker, or in a Markdown heading —
where it is invisible in the editor and breaks the tool that reads the file.

The rule has two companions that this check does not duplicate:

- `.editorconfig` sets `charset = utf-8`, so editors that honour it write UTF-8 in the first place.
- The `UP009` rule of `ruff` removes the `# -*- coding: utf-8 -*-` declarations, which are unnecessary once every file is UTF-8.

## Testing against input that is not UTF-8

The rule constrains what the repository *stores*, not what the code must *handle*. Renaissance.Py reads source files that it did
not write, so how it behaves on a Latin-1 or UTF-16 input — decode it, reject it with a clear message, or skip it — is behaviour
that deserves tests like any other.

Write such a test so that it builds its own input instead of committing a fixture:

```python
def test_a_latin_1_source_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "legacy.c"
    source.write_bytes("int sécurité;\n".encode("latin-1"))
    ...
```

Passing the bytes straight to the function under test works as well, when it does not need a file. Both stay outside `git`, so the
guard rail never sees them.

A fixture that is committed is not an option, and there is deliberately no allowlist for one: the check would fail, and every
other tool in the pipeline would trip over the file too. Generating the input is also the clearer test, because the bytes that
drive it are visible in the test, rather than hidden in a file that no editor can open without guessing.

## Running it

```powershell
python -m tools.check_encoding
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything, so both
invocations behave identically.

The files to inspect come from `git ls-files`, so generated and ignored output such as `site/` and `.venv/` is left alone, and a
file is checked from the moment it is staged. Files that contain a NUL byte in their first 8000 bytes are skipped: that is the
heuristic `git` itself uses to call a blob binary, and a binary file has no encoding to check. A UTF-16 file is recognised by its
byte order mark before that heuristic runs, so its NUL bytes cannot disguise it as binary.

Exit codes:

| Code | Meaning                                                                        |
| ---- | ------------------------------------------------------------------------------ |
| 0    | every tracked text file is UTF-8 without a byte order mark                     |
| 1    | at least one file is not                                                       |
| 2    | the files could not be listed, for example because `git` is not on the `PATH`  |

## Reading its output

Every violation is reported on one line, naming the file relative to the repository root and what is wrong with it:

```text
These files are not UTF-8 encoded:
  features/targets/main.c: not valid UTF-8: byte 0xe9 at offset 142 (invalid continuation byte)
  docs/developer/index.md: starts with a UTF-8 byte order mark
```

For a file that does not decode, the offset is the first byte that cannot be part of a UTF-8 sequence, which is where the editor
has to be pointed. For a byte order mark, the name of the mark says which encoding the file was saved as.

## Fixing a reported file

Re-save the file as UTF-8 without a byte order mark. In VS Code, use **Save with Encoding** from the encoding indicator in the
status bar after **Reopen with Encoding** has shown the text correctly; from PowerShell, the equivalent is:

```powershell
$text = Get-Content -Raw -Encoding Latin1 path/to/file
Set-Content -Path path/to/file -Value $text -Encoding utf8NoBOM
```

Check the result: a file that was already mojibake on disk needs the encoding it was *written* with, not the one it looks like.
