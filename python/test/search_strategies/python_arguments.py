# arguments_from_recursive.py
from __future__ import annotations

import ast
import keyword
import string
from typing import Any, Optional

from hypothesis import strategies as st
from hypothesis.strategies import composite, DrawFn

# Import your recursive generator & config
from python_type_and_value import (
    recursive_type_and_value_generator,
    RecGenConfig,
)

# ----------------------------
# Identifier generation (unique, valid Python names)
# ----------------------------

_FIRST = st.sampled_from(string.ascii_letters + "_")
_REST = st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=0, max_size=20)
IDENTIFIER = st.builds(str.__add__, _FIRST, _REST).filter(lambda s: not keyword.iskeyword(s))


# ----------------------------
# Helpers to build ast.arg with optional annotation
# ----------------------------

def _make_arg(name: str, annotation: Optional[ast.expr]) -> ast.arg:
    # Python 3.14: ast.arg has fields ('arg', 'annotation', 'type_comment'?)
    # We set type_comment=None if present, else ignore.
    fields = getattr(ast.arg, "_fields", ())
    kwargs : dict[str, Any] = {"arg": name}
    if "annotation" in fields:
        kwargs["annotation"] = annotation
    if "type_comment" in fields:
        kwargs["type_comment"] = None
    return ast.arg(**kwargs)


# ----------------------------
# Main strategy: build ast.arguments using the recursive type/value generator
# ----------------------------

@composite
def arguments_from_recursive(
    draw : DrawFn,
    # Size controls for parameter counts
    max_posonly: int = 2,
    max_args: int = 3,
    max_kwonly: int = 3,
    # Whether *vararg/**kwarg may be present
    allow_vararg: bool = True,
    allow_kwarg: bool = True,
    # Probability toggles for annotations and kw-only defaults
    p_annotate_nonpos: float = 0.5,  # probability to annotate non-tail positional or kw-only
    p_kwonly_default: float = 0.5,   # probability a kw-only arg gets a default
    # Config for the recursive type/value generator
    rec_config: RecGenConfig = RecGenConfig(),
) -> ast.arguments:
    """
    Produce an ast.arguments node where:
      - Names are unique across posonlyargs, args, kwonlyargs, vararg, kwarg.
      - For positional-only and positional-or-keyword params:
          * A random number N of trailing params (tail) get defaults.
          * For those N tail params: each either has a default-only OR both (annotation + matching default).
          * For non-tail: optional annotation, no default.
      - For kw-only params: optional annotation and optional default (independent),
        and when both are present the default matches the annotation type.
      - *vararg/**kwarg may be present; they can be annotated (no defaults).
      - Default values are built using the recursive generator, so nested containers,
        unions, dicts, etc., are supported. With the default RecGenConfig, empty
        containers are included in the search space.
    """

    # --- draw parameter counts ---
    n_pos = draw(st.integers(min_value=0, max_value=max_posonly))
    n_args = draw(st.integers(min_value=0, max_value=max_args))
    n_kwonly = draw(st.integers(min_value=0, max_value=max_kwonly))

    use_vararg = allow_vararg and draw(st.booleans())
    use_kwarg = allow_kwarg and draw(st.booleans())

    total_param_names = n_pos + n_args + n_kwonly + (1 if use_vararg else 0) + (1 if use_kwarg else 0)
    names = draw(st.lists(IDENTIFIER, min_size=total_param_names, max_size=total_param_names, unique=True))
    name_iter = iter(names)

    # --- recursive (type, value-gen) strategy to use when needed ---
    typed_value_pair = recursive_type_and_value_generator(rec_config)

    # --- positional defaults planning ---
    total_positional = n_pos + n_args
    n_defaults = draw(st.integers(min_value=0, max_value=total_positional))
    tail_start = total_positional - n_defaults  # indices >= tail_start must have a default

    # We'll build positional params first, tracking annotations and collecting defaults in order
    posonlyargs: list[ast.arg] = []
    args: list[ast.arg] = []
    positional_params_anns: list[Optional[ast.expr]] = []
    positional_defaults: list[ast.expr] = []  # exactly N defaults in left-to-right order of the tail

    # ---- build combined sequence of positional-only + args ----
    for i in range(total_positional):
        in_tail = i >= tail_start

        if in_tail:
            # Allowed cases: "default-only" OR "both"
            both = draw(st.booleans())  # decide if we include annotation + matching default
            if both:
                # Draw a (type, value-gen) pair; draw a value to form the default
                type_expr, val_gen = draw(typed_value_pair)
                default_expr = draw(val_gen)
                positional_params_anns.append(type_expr)
                positional_defaults.append(default_expr)
            else:
                # default-only (no annotation)
                _type_expr, val_gen = draw(typed_value_pair)
                default_expr = draw(val_gen)
                positional_params_anns.append(None)
                positional_defaults.append(default_expr)
        else:
            # Non-tail cannot have defaults; may have annotation
            if draw(st.randoms()).random() < p_annotate_nonpos:
                type_expr, _ = draw(typed_value_pair)
                positional_params_anns.append(type_expr)
            else:
                positional_params_anns.append(None)

    assert len(positional_defaults) == n_defaults

    # Now build ast.arg nodes for posonly and args
    # First n_pos belong to posonly
    for i in range(n_pos):
        name = next(name_iter)
        ann = positional_params_anns[i]
        posonlyargs.append(_make_arg(name, ann))

    # The remaining belong to args
    for j in range(n_args):
        idx = n_pos + j
        name = next(name_iter)
        ann = positional_params_anns[idx]
        args.append(_make_arg(name, ann))

    # --- kw-only params ---
    kwonlyargs: list[ast.arg] = []
    kw_defaults: list[Optional[ast.expr]] = []

    for _ in range(n_kwonly):
        name = next(name_iter)

        do_ann = draw(st.randoms()).random() < p_annotate_nonpos
        do_default = draw(st.randoms()).random() < p_kwonly_default

        if do_ann and do_default:
            # both: matching type and default
            type_expr, val_gen = draw(typed_value_pair)
            default_expr = draw(val_gen)
            kwonlyargs.append(_make_arg(name, type_expr))
            kw_defaults.append(default_expr)
        elif do_ann:
            type_expr, _ = draw(typed_value_pair)
            kwonlyargs.append(_make_arg(name, type_expr))
            kw_defaults.append(None)
        elif do_default:
            # default-only
            _type_expr, val_gen = draw(typed_value_pair)
            default_expr = draw(val_gen)
            kwonlyargs.append(_make_arg(name, None))
            kw_defaults.append(default_expr)
        else:
            # neither
            kwonlyargs.append(_make_arg(name, None))
            kw_defaults.append(None)

    # --- *vararg / **kwarg (optional annotation; no defaults) ---
    vararg: Optional[ast.arg] = None
    if use_vararg:
        name = next(name_iter)
        if draw(st.booleans()):         # TODO: why no probability toggle here?
            type_expr, _ = draw(typed_value_pair)
            vararg = _make_arg(name, type_expr)
        else:
            vararg = _make_arg(name, None)

    kwarg: Optional[ast.arg] = None
    if use_kwarg:
        name = next(name_iter)
        if draw(st.booleans()):         # TODO: why no probability toggle here?
            type_expr, _ = draw(typed_value_pair)
            kwarg = _make_arg(name, type_expr)
        else:
            kwarg = _make_arg(name, None)

    # --- assemble ast.arguments ---
    return ast.arguments(
        posonlyargs=posonlyargs,
        args=args,
        vararg=vararg,
        kwonlyargs=kwonlyargs,
        kw_defaults=kw_defaults,
        kwarg=kwarg,
        defaults=positional_defaults,  # must correspond to the LAST N positional params
    )