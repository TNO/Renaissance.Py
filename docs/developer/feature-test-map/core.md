# Core feature ↔ test mappings

## 1. Pattern matching

- **Feature:** [Pattern matching](../../user/features/pattern-matching.md)
- **Suggested test modules:** `tests/matching/`

## 2. Rewrite semantics

- **Feature:** [Rewrite semantics](../../user/features/rewrite-semantics.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- **Test modules:** [Rewrite semantics test module](../../developer/modules/rewrite-semantics.md)
- **BDD feature file:** `features/rewrite-semantics.feature`
- **BDD steps:** `features/steps/test-rewrite-semantics.py`
- **Code files:** `src/renaissance/common/rewriter.py`, `src/renaissance/syntax_tree/ast_rewriter.py`

## 3. TypeVar modernization

- **Feature:** [TypeVar modernization](../../user/features/typevar-modernization.md)
- **Concepts:** [Type parameter scope](../../user/concepts/type-parameter-scope.md)
- **Code modules:** [Refactoring recipes](../../developer/modules/recipes.md)
- **Test file(s):**
  - `test/recipes/test_type_var_check.py`
  - `test/recipes/test_type_var_check_convert.py`
  - `test/recipes/test_type_var_check_localize.py`
  - `test/recipes/test_type_var_check_orphaned.py`
  - `test/recipes/test_type_var_check_properties.py`
  - `test/recipes/test_type_var_tuple_check.py`
  - `test/recipes/test_type_var_tuple_check_fix.py`
  - `test/recipes/test_type_var_tuple_check_properties.py`
  - `test/recipes/test_type_var_domain.py`
- **Code file(s):** `src/renaissance/recipes/type_var_check.py`, `src/renaissance/recipes/type_var_tuple_check.py`,
  `src/renaissance/recipes/type_var_domain.py`
