# Copyright check

`tools/check_copyright.py` keeps the copyright notice of `COPYRIGHT.txt` at the top of every file that git tracks. It checks the
notice, inserts it where it is missing, and removes it again.

## The rule it enforces

`COPYRIGHT.txt` in the repository root is the single source of truth for the notice. Every tracked file carries that notice exactly,
written as a comment in the style of its file type:

- `.py`, `.toml`, `.yml`, `.feature` and `.gitignore` files: every line prefixed by `#` and a space; an empty notice line becomes a
  bare `#`;
- `.md` files: one HTML comment, with its opening `<!--` and its closing `-->` on lines of their own.

The notice is the first thing in the file. Only the lines that must stay first may precede it, in this order:

1. a UTF-8 byte order mark;
1. a shebang (`#!`) on the first line;
1. a Python encoding declaration ([PEP 263](https://peps.python.org/pep-0263/)), on line 1, or on line 2 below a blank or
   comment-only line, because Python only reads it there;
1. a Gherkin `# language:` line in a `.feature` file;
1. front matter (`---` up to `---` or `...`) in a Markdown file.

Exactly one blank line separates the notice from the rest of the file; an empty file holds the notice and nothing else.
A Python script with a shebang and an encoding declaration therefore starts like this:

```python
#!/usr/bin/env python
# -*- coding: latin-1 -*-
# <first line of COPYRIGHT.txt>
#
# <third line of COPYRIGHT.txt>

"""Module docstring."""
```

Ruff's `CPY001` rule recognises the result as a copyright notice by `TNO`, as configured in `[tool.ruff.lint.flake8-copyright]`.

### Which files

Only files that git tracks are considered. Two kinds of tracked files are skipped:

- the files matched by `EXCLUDED` in the script, each with the reason: files without comment syntax (JSON, `docs/TODO`), binary
  files, generated files (`uv.lock`), and legal texts that must stay as they are (`LICENSE`, `CLA.md`, `COPYRIGHT.txt` itself);
- the test inputs, listed under `[tool.ruff] extend-exclude` in `pyproject.toml`. Tests may assert their content, including line
  numbers, so neither Ruff nor any guard rail may change them. The script reads Ruff's list and matches it the way Ruff does: a
  pattern without a slash matches any path component, a pattern with a slash matches from the repository root, and a directory
  covers everything below it. Because the list is shared, it must hold test inputs only.

A tracked file whose type is neither in `COMMENT_STYLES` nor excluded fails the check, so a new file type is a deliberate decision.
A pattern in `EXCLUDED` or `extend-exclude` that matches no tracked file fails the check as well, so the lists cannot outlive the
files they describe.

## Running it

```powershell
python tools/check_copyright.py check
python tools/check_copyright.py insert
python tools/check_copyright.py remove
```

- `check` reports every file that does not carry the notice exactly, and writes nothing. CI runs it.
- `insert` adds the notice to every file that lacks it. A file that already carries the notice is left alone.
- `remove` deletes the exact current notice, and the blank line after it, from every file that carries it. A file without the notice
  is left alone.

All three commands accept files or directories, which limits the run to the tracked files among them, for example
`python tools/check_copyright.py insert tools/my_new_tool.py`. A path that git does not track is a usage error.

`insert` and `remove` preserve everything else about a file: its encoding (the declared PEP 263 encoding for Python, UTF-8
otherwise), its byte order mark, its line endings (LF, CRLF or CR) and whether it ends in a newline. `insert` followed by `remove`
restores the original bytes, and running either command twice changes nothing the second time. Neither command touches a file
with a problem it cannot fix safely, such as a modified notice; it reports the file instead.

Exit codes:

| Code | Meaning                                                                                                        |
| ---- | -------------------------------------------------------------------------------------------------------------- |
| 0    | every file carries the notice (`check`), or every file could be updated (`insert`, `remove`)                   |
| 1    | a file violates the rule and could not be fixed, or an exclusion pattern matches no tracked file               |
| 2    | the tool could not run: invalid arguments, an unusable `COPYRIGHT.txt` or `pyproject.toml`, a git or I/O error |

## Reading its output

Every changed file and every violation is reported on one line, sorted by path, followed by a summary:

```text
tools/new_tool.py: notice missing
Copyright check failed: 1 violation(s); see docs/developer/tools/check-copyright.md.
```

What to do for each reason:

- `notice missing`: run `insert`.
- `notice modified or outdated`: the header holds another copyright notice; see [Changing the notice](#changing-the-notice).
- `notice at the wrong position`: move the notice to the top, or delete it and run `insert`.
- `notice in the wrong comment style or layout`: delete the notice and run `insert`.
- `notice not followed by a blank line` or `by a line ending`: add the blank line.
- `notice above a shebang or encoding declaration`: move the shebang or the declaration above the notice, where it works again.
- `unmapped file type`: add the type to `COMMENT_STYLES`, or the file to `EXCLUDED` with the reason.
- `exclusion pattern matches no tracked file`: delete the pattern.
- `mixed line endings` and encoding problems: fix the file; the tool does not guess how it should be written.

## Changing the notice

`remove` only recognises the exact current notice, so a change goes in three steps:

1. `python tools/check_copyright.py remove`
1. edit `COPYRIGHT.txt`
1. `python tools/check_copyright.py insert`

If `COPYRIGHT.txt` was edited first, the files now hold a notice that differs from it, which `check` and `insert` report as modified
or outdated. To recover, restore the previous version with `git restore COPYRIGHT.txt` (or `git show HEAD:COPYRIGHT.txt`), run
`remove`, apply the edit again, and run `insert`.

`COPYRIGHT.txt` must start with a non-empty line and must not contain trailing whitespace or `-->`, which would end the comment in
Markdown files; otherwise the tool stops with exit code 2 before it touches a file.
