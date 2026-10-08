# Layering check

`tools/check_layering.py` fails the build when a module imports another module that it is not allowed to depend on.

## The rule it enforces

The source tree is divided into layers, and a layer may only import the layers below it.

| Layer | Packages | May import |
| --- | --- | --- |
| `core` | `renaissance.syntax_tree`, `renaissance.common`, `renaissance.utils` | nothing outside the core |
| `parser_bindings` | `renaissance.integrations` | `core` |
| `recipes` | `renaissance.recipes`, `rejuvenation` | `core`, `parser_bindings` |

Imports within a layer are always allowed, and imports of the standard library or of third-party packages are ignored.

The direction matters because the core carries the language- and parser-agnostic machinery: the AST abstraction, pattern matching,
rewriting and recipe execution. A parser binding connects one concrete parser to that machinery, and a recipe expresses an analysis
or a transformation in terms of it. As long as the core never reaches back into a binding, a binding can be added, replaced or
removed without touching the core, and a recipe can run against any parser that provides the abstractions the core defines. One
import in the wrong direction silently removes that property: the core then only works when that particular parser is installed
and importable.

## Running it

```powershell
python tools/check_layering.py
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything, so both
invocations behave identically. The script only parses the sources, it never imports them, so a parser binding whose external
dependency is missing cannot make the check fail or pass by accident.

Exit codes:

| Code | Meaning |
| --- | --- |
| 0 | every violation found is covered by the allowlist |
| 1 | a violation is not allowlisted, or an allowlist entry no longer matches a violation |
| 2 | the sources could not be analysed, for example because a file does not parse |

## Reading its output

Every violation is reported on one line, naming the file and the line number so that terminals and CI logs can link to it:

```text
src\renaissance\utils\ast_utils.py:7: renaissance.utils.ast_utils (core) imports renaissance.integrations (parser_bindings)
```

Violations are reported wherever they are written: at the top of a module, inside a function body, inside a `try` block, and inside
an `if TYPE_CHECKING:` block. The last kind is marked `[type-checking only]`. Such an import does not exist at run time, but it is
still a design dependency — the core cannot be type-checked, documented or understood without the binding — so it is reported like
any other.

Relative imports are resolved against the package of the importing module before they are judged, so `from ..integrations import x`
is reported as an import of `renaissance.integrations`.

## The allowlist

Violations that are known and accepted for now are listed in the `ALLOWLIST` of the script, each with the module, the imported
module and the reason it still exists. An allowlisted violation is printed on every run, under a heading that says it is to be
resolved, but it does not fail the check. This keeps the build green while the problem stays visible.

Two properties keep the allowlist from becoming a dumping ground:

1. An entry names one importing module and one imported module exactly. Wildcards are not supported, so an entry can never cover a
   violation that was added later.
1. An entry that no longer matches a violation fails the check. Once an import is removed, the next run tells you to delete its
   entry, so the allowlist cannot outlive the problem it describes.

Add an entry only when the fix is a design change that does not belong in the pull request at hand, and record *why* in the reason.
The preferred fix is almost always to move the abstraction the core needs into the core, and to let the binding implement it.

## When the packages are renamed

The layer definitions are the `LAYERS` and `ALLOWED_DEPENDENCIES` mappings at the top of the script. `LAYERS` maps a layer name to
the packages it owns, and `ALLOWED_DEPENDENCIES` maps a layer name to the other layers it may import. Renaming or moving a package
is a one-line edit to `LAYERS`; introducing a layer is one entry in each mapping. Nothing else in the script knows the package
names, and the tests run against synthetic package trees rather than against `src`, so they keep working across a restructuring.

After a rename, run the check: the modules whose allowlist entries still carry the old names will be reported as stale, which is
the signal to update or delete them.
