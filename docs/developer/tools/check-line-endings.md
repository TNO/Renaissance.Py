# Line ending check

`tools/check_line_endings.py` fails the build when git stores a text file in the repository with CRLF line endings, or with a mix
of LF and CRLF.

## The rule it enforces

Every text file in the repository ends its lines with LF, both in what git stores and in what a checkout writes to disk, on Windows
as well as on Linux.

LF is what the Python ecosystem, GitHub and the Ubuntu runners of CI assume. One line ending for everybody also keeps the working
tree byte-identical across platforms, which matters more here than in most projects: Renaissance.Py analyses source files, so a
line ending is input data. A `\r` changes the byte offsets a parser reports and ends up in the text it extracts, so a test against
a file in `features/targets` must not depend on the platform it was checked out on.

## How the rule is enforced

The rule is enforced in layers; this check is the last one.

1. `.gitattributes` sets `* text=auto eol=lf`. Git converts CRLF to LF when a text file is committed and writes LF on checkout,
   whatever `core.autocrlf` a contributor has configured. `text=auto` lets git recognise binary files; the images and the
   PowerPoint file are also marked `binary` explicitly.
1. `.editorconfig` sets `end_of_line = lf`, and `.vscode/settings.json` sets `files.eol` to `\n`, so editors write LF in the first
   place. VS Code only reads `.editorconfig` with the EditorConfig extension, which is why both exist.
1. The `[tool.ruff.format]` section of `pyproject.toml` sets `line-ending = "lf"`, so `ruff format` writes LF on Windows as well;
   its default keeps whatever ending a file already has.
1. This check fails the build when a text file is stored with CRLF anyway.

Given the attribute, git cannot store CRLF in a text file, so the check is a backstop. It catches what the attribute cannot see: a
file committed before the attribute existed, for example on a long-lived branch, and an edit of `.gitattributes` that weakens or
removes the rule.

## Testing against input with other line endings

The rule constrains what the repository *stores*, not what the code must *handle*. Renaissance.Py reads source files that it did
not write, and those come with CRLF, with LF, and with a mix of both; how the code behaves on each of them deserves tests like any
other behaviour.

There is one difference with the [encoding check](check-encoding.md) that makes this easy to get wrong: git does not reject a
CRLF fixture, it *converts* it. A CRLF file committed under `eol=lf` is silently stored as LF, so the test keeps passing while it
tests LF input, and nobody notices.

### Generate the input in the test

This is the preferred way, because the bytes that drive the test are visible in the test and no checkout can change them:

```python
def test_a_crlf_source_is_parsed(tmp_path: Path) -> None:
    source = tmp_path / "input.c"
    source.write_bytes(b"int a;\r\nint b;\r\n")
    ...
```

Passing the bytes straight to the function under test works as well, when it does not need a file.

Mind Python's newline translation, which applies to text mode on both sides:

- `Path.write_text("a\r\nb")` writes `a\r\r\nb` on Windows, because text mode turns every `\n` into `\r\n`. Use `write_bytes`, or
  `write_text(..., newline="")`, which writes the string as it is.
- `Path.read_text()` turns every `\r\n` and every `\r` into `\n`, so a test that reads back what it wrote cannot see the line
  endings. Use `read_bytes`, or `open(..., newline="")`, when the line endings are what the test is about.

### Commit a fixture only when it cannot be generated

When a file really has to be committed with CRLF, for example a large sample taken from a real code base, put it in a directory of
its own and switch off the conversion for that directory in `.gitattributes`:

```gitattributes
test/test_data/line-endings/** -text
```

Git then stores the bytes verbatim, and this check skips files marked `-text`. Keep that exception narrow: a directory that holds
only such fixtures, never a pattern by file extension, so that no ordinary source file can fall under it. The fixture must still be
UTF-8; the encoding check applies to it like to any other file.

## Running it

```powershell
python tools/check_line_endings.py
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything, so both
invocations behave identically.

The check reads the index through `git ls-files --eol`, so it inspects exactly what would be committed, and leaves untracked and
ignored files alone. The working tree is not checked: git converts it on every commit, and an old clone may legitimately still hold
CRLF files, see below.

Exit codes:

| Code | Meaning                                                                         |
| ---- | ------------------------------------------------------------------------------- |
| 0    | every tracked text file is stored with LF, or has no line ending at all         |
| 1    | at least one text file is stored with CRLF or with mixed line endings           |
| 2    | the files could not be listed, for example because `git` is not on the `PATH`   |

## Reading its output

Every violation is reported on one line, naming the file relative to the repository root and the line endings git stored:

```text
These files are not stored with LF line endings:
  tools/example.py: stored with CRLF line endings
  docs/example.md: stored with a mix of LF and CRLF line endings
```

## Fixing a reported file

With `.gitattributes` in place, let git convert the files and commit the result:

```powershell
git add --renormalize .
git commit -m "Normalize line endings to LF"
```

When the check fails although `.gitattributes` exists, look at the attributes git applied to the file first, because a later line
in `.gitattributes` may override the rule for it:

```powershell
git check-attr text eol -- path/to/file
```

## Updating a clone made before the rule

Git does not rewrite files on disk that it considers unchanged, so a clone made before `.gitattributes` existed keeps its CRLF
files until they are checked out again. Nothing is committed wrongly, but `ruff format --check` reports such Python files, and
tests that read files as bytes may see `\r`. With nothing left to commit or stash, check them out again from the index:

```powershell
$files = git ls-files --eol | Select-String 'w/(crlf|mixed)' | ForEach-Object { ($_.Line -split "`t", 2)[1] }
Remove-Item -LiteralPath $files
git checkout -- $files
```
