<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core feature ↔ test mappings

## 1. Pattern matching

- **Feature:** [Pattern matching](../../user/features/pattern-matching.md)
- **Test file(s):**
    - `test/syntax_tree/test_match_finder.py`
    - `test/syntax_tree/test_match_finder_multi_assignments.py`
    - `test/syntax_tree/test_match_tree.py`
    - `test/syntax_tree/test_match_dict.py`
    - `test/syntax_tree/test_pattern_match.py`
    - `test/syntax_tree/test_pattern_kind.py`
    - `test/python/ast/test_python_matcher.py`
    - `test/c_cpp/test_c_match_finder.py`
- **Code file(s):** `src/renaissance/syntax_tree/match_finder.py`, `src/renaissance/syntax_tree/pattern_kind.py`

## 2. Rewrite semantics

- **Feature:** [Rewrite semantics](../../user/features/rewrite-semantics.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- **Test modules:** [Rewrite semantics test module](../../developer/modules/rewrite-semantics.md)
- **BDD feature file:** `features/rewrite-semantics.feature`
- **BDD steps:** `features/steps/test_rewrite_semantics.py`
- **Test file(s):**
    - `test/common/test_rewriter.py`
    - `test/syntax_tree/test_ast_rewriter.py`
    - `test/syntax_tree/test_rewrite_semantics_properties.py`
- **Code files:** `src/renaissance/common/rewriter.py`, `src/renaissance/syntax_tree/ast_rewriter.py`

## 3. Type parameter modernization

- **Feature:** [Type parameter modernization](../../user/features/type-parameter-modernization.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- **Code modules:** [Refactoring recipes](../../developer/modules/recipes.md)
- **Test file(s):**
    - `test/recipes/test_type_parameter_check.py`
    - `test/recipes/test_type_parameter_check_convert.py`
    - `test/recipes/test_type_parameter_check_localize.py`
    - `test/recipes/test_type_parameter_check_orphaned.py`
    - `test/recipes/test_type_parameter_check_properties.py`
    - `test/recipes/test_type_parameter_check_variance.py`
    - `test/recipes/test_type_parameter_rules.py`
    - `test/recipes/test_step_runner.py`
    - `test/recipes/test_python_refactoring.py`
    - `test/utils/test_import_resolution.py`
    - `test/rejuvenation/test_migration_type_recipes.py`
- **Code file(s):** `src/renaissance/recipes/type_parameter_check.py`, `src/renaissance/recipes/type_parameter_rules.py`,
  `src/renaissance/recipes/step_runner.py`,
  `src/renaissance/recipes/python_refactoring.py`,
  `src/renaissance/utils/import_resolution.py`, `src/rejuvenation/migration-type-recipes.py`
