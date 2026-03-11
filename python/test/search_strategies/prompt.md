You are to generate Python code (Python 3.14 only) that provides Hypothesis strategies to generate:
  1) (type_expr: ast.expr, value_gen: SearchStrategy[ast.expr]) pairs, where value_gen lazily produces an ast.expr value matching type_expr.
  2) an ast.arguments generator for function definitions using those (type_expr, value_gen) pairs (optional but desirable).

STRICT CONSTRAINTS / CONVENTIONS
A) Python 3.14-only codebase:
   - Do NOT use: from __future__ import annotations
   - Do NOT use typing.List / typing.Optional. Use built-in generics: list[T], dict[K,V], tuple[...] and union types: X | None.
   - Type hints should use `list[...]`, `dict[...]`, `tuple[...]`, `ast.expr | None`.
B) Hypothesis typing:
   - Every @composite strategy must type its draw parameter as DrawFn.
   - The module must import DrawFn: `from hypothesis.strategies import DrawFn`.
C) Naming / structure:
   - Provide a uniform generator family with these PUBLIC functions only:
       gen_type, gen_base, gen_list, gen_dict, gen_union, gen_tuple
     Do NOT add separate list_type_and_value / dict_type_and_value / union_type_and_value / tuple_type_and_value wrappers.
     Focused tests should call gen_list/gen_union/gen_dict/gen_tuple directly.
   - Do NOT pass a SearchStrategy “child” parameter around. The generators must call gen_type(depth-1) internally.
D) Builders:
   - All AST node construction helpers must be PRIVATE and start with `_build_`.
     Example: use `_build_arg`, NOT `_make_arg`.
   - Group all `_build_*` helpers together in one section.
E) Size policy:
   - Provide one function: `max_len(depth: int) -> int` that returns `3 * depth`.
   - NEVER inline `3 * depth` anywhere; always call max_len(depth).
   - Lists/tuples/dicts must allow empty values (min size = 0).
   - Unions must have minimum arms 2.
F) Union special-cases (must live inside gen_union):
   - If depth <= 1: max number of union arms is 2 (so unions are exactly 2 arms at these depths).
   - Else: max number of union arms is max_len(depth).
   - Additionally: for depth <= 2, union arms must be base types only (i.e., generated from gen_base at “depth=0”).
G) Performance / energy:
   - When building the BitOr chain for union type expressions, avoid list slicing copies; use `islice` from itertools where appropriate.
H) Dict typing correctness:
   - Use this builder exactly (or functionally identical):
       def _build_dict(keys: list[ast.expr], values: list[ast.expr]) -> ast.Dict:
           return ast.Dict(keys=list(keys), values=values)
     Rationale: ast.Dict.keys accepts list[expr | None], list is invariant; we copy keys to satisfy typing.
I) Base types:
   - Must include these base type names: bool, int, str, float, bytes, NoneType.
   - NoneType must generate the instance `None` (as an ast.Constant(value=None)).
   - Base type_expr must be ast.Name(id=..., ctx=Load()) using those names. (We only need AST validity; runtime execution is not required.)

REQUIRED OUTPUT API
1) max_len(depth: int) -> int
2) gen_base(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
3) gen_list(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
4) gen_dict(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
5) gen_union(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
6) gen_tuple(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
7) gen_type(draw: DrawFn, depth: int) -> tuple[ast.expr, SearchStrategy[ast.expr]]
   - gen_type must dispatch among ALL five types: base, list, dict, union, tuple.
   - If depth <= 0, gen_type must return a base pair (by drawing from gen_base(0) or equivalent).
   - Otherwise, gen_type must draw from one_of(gen_base(depth), gen_list(depth), gen_dict(depth), gen_union(depth), gen_tuple(depth)).

LAZINESS REQUIREMENT
- Every gen_* returns (type_expr, value_gen_strategy). value_gen must be a SearchStrategy[ast.expr] that generates the matching AST value.
- Do not eagerly draw a value in the generator unless unavoidable. Prefer to return a composed strategy, e.g., st.lists(elem_vg, ...).map(_build_list).

NON-VERBOSE STYLE
- Keep the code short and readable; avoid excessive scaffolding.
- Avoid redundant checks that are already handled by gen_type(depth-1).
- Do not introduce config objects or include_* boolean flags.

TESTS (MUST GENERATE)
Produce a separate test module (pytest + hypothesis) with tests that verify each generator produces what it promises:
1) test_gen_list_generates_list:
   - data.draw(gen_list(depth)) returns type_expr that is ast.Subscript with value ast.Name('list')
   - value_expr = data.draw(value_gen) is ast.List
2) test_gen_dict_generates_dict:
   - type_expr is ast.Subscript with value ast.Name('dict')
   - value_expr is ast.Dict and len(keys)==len(values)
   - keys are ast.Constant (or None if you later add ** unpacking; currently should be Constant)
3) test_gen_tuple_generates_tuple:
   - type_expr is ast.Subscript with value ast.Name('tuple')
   - value_expr is ast.Tuple
   - empty tuple must be reachable (not necessarily always)
4) test_gen_union_generates_union:
   - type_expr is a BinOp chain with BitOr (at least one BinOp at root)
   - flatten leaves; number of leaves:
       - if depth <= 1 => exactly 2
       - if depth > 1 => between 2 and max_len(depth)
     and if depth <= 2 all leaves must be ast.Name of base types only (including NoneType).
   - value_expr = data.draw(value_gen) must be ast.expr
   - additionally for depth <= 2, since arms are base types, value_expr should be ast.Constant whose underlying Python value type matches one of the union arms:
       bool->bool, int->int, str->str, float->float, bytes->bytes, NoneType->NoneType (type(None)).
5) test_smoke_compile:
   - for depth=0, for each gen_base/gen_list/gen_dict/gen_union/gen_tuple, build an annotated assignment:
       x: <type_expr> = <value_expr>
     wrap in ast.Module and compile() it. Compilation must succeed.
   - Note: execution is not required.

IMPORTANT: OUTPUT FORMAT
- Produce the full code for the generator module in one code block.
- Produce the full code for the tests in a second code block.
- Do not output in tables.
- Do not add extra “focused wrapper” functions list_type_and_value/dict_type_and_value/union_type_and_value/tuple_type_and_value.
- Ensure all builder helpers are named _build_* and grouped together.