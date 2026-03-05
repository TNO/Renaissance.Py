You are working on a Python 3.14-only Hypothesis generator module that builds AST types and lazy value generators for use in property-based tests. The module generates pairs:

    (type_expr: ast.expr, value_gen: hypothesis.strategies.SearchStrategy[ast.expr])

and uses these pairs to synthesize ast.arguments for function definitions.

GOALS / DESIGN PRINCIPLES
1) Python 3.14 only. Do not add backwards compatibility.
2) Keep code non-verbose and readable. Prefer direct Hypothesis combinators and avoid unnecessary intermediate variables.
3) Provide separate PUBLIC generator functions for container/type constructors:
       - gen_list(child, depth)
       - gen_tuple(child, depth)
       - gen_union(child, depth)  [union min arms = 2]
       - gen_dict(child, depth)
   These must remain accessible for focused tests (e.g., union-only test suites).
4) Avoid include_* boolean configuration flags. Use focused dispatchers (e.g., union_type_and_value(depth)) or direct calls to gen_* instead.
5) Minimal lengths must be 0 for lists, tuples and dicts (so empty list/tuple/dict corner cases are always reachable).
6) Unions must have minimum length 2. (No empty union type; no 1-arm union.)
7) Use ONE function for max sizes based on depth:
       max_len(depth) = 3 * depth
   Use it consistently for list lengths, tuple arity, dict size, union arms, and any future container sizes.
8) Maintain laziness: value_gen should generally remain a strategy so values are generated only when needed, supporting shrinking.
   Note: some constructors may temporarily materialize values inside @composite, but prefer returning a strategy for values whenever possible.

AST SHAPE REQUIREMENTS (PYTHON 3.14)
- Base scalar types are represented as ast.Name('int'|'str'|'bool'|'float'|'bytes') with ctx=Load.
- list[T], tuple[...], dict[K, V] are represented using ast.Subscript with ast.Name('list'/'tuple'/'dict') as value.
- For tuple types:
    - non-empty: tuple[T1, T2, ...]   -> Subscript(slice=ast.Tuple([T1, T2, ...]))
    - empty tuple type: tuple[()]      -> slice must be a 1-tuple containing an empty ast.Tuple:
         Subscript(slice=ast.Tuple([ast.Tuple([])]))
  The corresponding empty tuple value is ast.Tuple([]).
- Union types use PEP 604 syntax via AST binop:
     T1 | T2 | ... -> left-associative ast.BinOp(op=ast.BitOr())
  union constructor MUST enforce >= 2 arms.

DICT KEYS
- dict keys should remain hashable at runtime. Current design restricts key types to base scalar types.
- If extending to allow tuple keys, only allow tuples made of hashable elements (e.g., tuples of base scalars), and keep max size bounded by depth via max_len.

ARGUMENTS GENERATOR REQUIREMENTS
- Must generate ast.arguments with all combinations of:
    posonlyargs, args, kwonlyargs, optional vararg (*args), optional kwarg (**kwargs).
- Enforce uniqueness of argument names across all these categories.
- Defaults:
    - positional defaults must apply to the last N of (posonlyargs + args) as per Python AST rules.
    - kw_defaults length must equal kwonlyargs length; entries are ast.expr or None.
- Annotations and defaults:
    - Each parameter may have annotation and/or default.
    - When both are present, the default value must be generated from the same (type_expr, value_gen) pair as the annotation to ensure type-consistency.
- Corner cases should be reachable, including empty defaults for containers ([], {}, ()).

EXTENSION GUIDELINES
- If adding new container types (e.g., set[T], frozenset[T], dict with tuple keys, nested unions, Optional, Literal, etc.):
    - Provide a separate public gen_* constructor, or a focused dispatcher, rather than adding include_* flags.
    - Ensure min length = 0 (unless there is a strong semantic reason to require otherwise; unions are the exception with min=2).
    - Ensure max size uses max_len(depth).
    - Keep AST representation valid for Python 3.14.
- If adding new base types, update:
    - BASE_VALUES mapping (type name -> SearchStrategy producing ast.expr values)
    - BASE_TYPE sampling strategy
- Always keep recursion depth bounded. Ensure depth decreases in recursive calls.
- Provide small sanity tests:
    - compile(ast.Module(ast.FunctionDef(...))) should succeed.
    - uniqueness of names should hold.
    - defaults layout invariants should hold.
    - union has >=2 arms.
  Prefer concise tests. Use ast.unparse for shape checks when useful.

STYLE
- Keep AST builder helpers private and prefixed _build_.
- Keep public generator constructors named gen_*.
- Keep dispatchers named *_type_and_value(depth) and type_and_value(depth).

TASK FOR THE ASSISTANT WHEN MODIFYING THIS MODULE
- Propose minimal edits only; do not rewrite everything unless required.
- Preserve the design principles above.
- If you change AST shapes, update tests and explain the reason concisely.
- If you introduce any new constraint, document it at the top of the module.

Deliver updated code snippets (not in tables) and, when relevant, small focused tests.