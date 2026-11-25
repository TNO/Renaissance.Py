<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core feature ↔ test mappings

## 1. Pattern matching

- **Feature:** [Pattern matching](../../user/features/pattern_matching.md)
- **Concepts:** [Pattern](../../user/core/pattern/pattern.md), [Match](../../user/core/match/match.md)
- **Code modules:** [Core pattern kind](../core/pattern/pattern_kind.md), [Core placeholders](../core/pattern/placeholders.md),
  [Core match finder](../core/match/match_finder.md)
- **Test file(s):**
    - `test/unit/core/match/test_match_finder___one_and_all_params.py`
    - `test/unit/core/match/test_match_finder___multi_assignments.py`
    - `test/unit/core/match/test_match_finder___match_tree.py`
    - `test/unit/core/match/test_match_finder___match_dict.py`
    - `test/unit/core/match/test_match_finder___pattern_match.py`
    - `test/unit/core/pattern/test_pattern_kind.py`
    - `test/unit/parser_bindings/python/ast/test_factory___matcher.py`
    - `test/unit/parser_bindings/python/ast/test_factory___type_parameters.py`
    - `test/unit/parser_bindings/python/ast/test_factory___keywords.py`
    - `test/c_cpp/test_c_match_finder.py`
- **Code file(s):** `src/renaissance/core/match/match_finder.py`, `src/renaissance/core/pattern/pattern_kind.py`,
  `src/renaissance/core/pattern/placeholders.py`, `src/renaissance/parser_bindings/python/ast/factory.py`

## 2. Rewrite semantics

- **Feature:** [Rewrite semantics](../../user/features/rewrite_semantics.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite_semantics.md), [Rewrite](../../user/core/rewrite/rewrite.md)
- **Code modules:** [Core AST rewriter](../core/rewrite/ast_rewriter.md), [Core rewriter](../core/rewrite/rewriter.md)
- **Test modules:** [Rewrite semantics test module](../architecture/modules/rewrite_semantics.md)
- **BDD feature file:** `features/rewrite_semantics.feature`
- **BDD steps:** `features/steps/test_rewrite_semantics.py`
- **Test file(s):**
    - `test/unit/core/rewrite/test_rewriter.py`
    - `test/unit/core/rewrite/test_ast_rewriter___comment_location.py`
    - `test/unit/core/rewrite/test_ast_rewriter___composition.py`
    - `test/unit/core/rewrite/test_ast_rewriter___remove_replace_insert.py`
    - `test/unit/core/rewrite/test_ast_rewriter___semantics.py`
- **Code files:** `src/renaissance/core/rewrite/rewriter.py`, `src/renaissance/core/rewrite/ast_rewriter.py`

## 3. Type parameter modernization

- **Feature:** [Type parameter modernization](../../user/features/type_parameter_modernization.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite_semantics.md)
- **Code modules:** [Refactoring recipes](../architecture/modules/recipes.md)
- **Test file(s):**
    - `test/recipes/test_type_parameter_check.py`
    - `test/recipes/test_type_parameter_check_convert.py`
    - `test/recipes/test_type_parameter_check_localize.py`
    - `test/recipes/test_type_parameter_check_orphaned.py`
    - `test/recipes/test_type_parameter_check_properties.py`
    - `test/recipes/test_type_parameter_check_variance.py`
    - `test/recipes/test_type_parameter_declarations.py`
    - `test/recipes/test_type_parameter_localization.py`
    - `test/recipes/test_type_parameter_rules.py`
    - `test/recipes/test_step_runner.py`
    - `test/recipes/test_python_refactoring.py`
    - `test/unit/parser_bindings/python/libcst/test_cst_utils.py`
    - `test/utils/test_import_resolution.py`
    - `test/recipes/test_ruff_utils.py`
    - `test/rejuvenation/test_migration_type_recipes.py`
- **Code file(s):** `src/renaissance/recipes/type_parameter_check.py`, `src/renaissance/recipes/type_parameter_rules.py`,
  `src/renaissance/recipes/type_parameter_declarations.py`, `src/renaissance/recipes/type_parameter_localization.py`,
  `src/renaissance/recipes/type_parameter_uses.py`,
  `src/renaissance/recipes/step_runner.py`,
  `src/renaissance/recipes/python_refactoring.py`,
  `src/renaissance/utils/import_resolution.py`, `src/renaissance/parser_bindings/python/libcst/cst_utils.py`,
  `src/renaissance/recipes/ruff_utils.py`,
  `src/rejuvenation/migration_type_recipes.py`

## 4. Navigation

- **Feature:** [Navigation](../../user/features/navigation.md)
- **Concepts:** [Navigate](../../user/core/navigate/navigate.md)
- **Code modules:** [Core navigate](../core/navigate/navigate.md), [Core navigation protocols](../core/navigate/protocols.md)
- **Test file(s):**
    - `test/unit/core/navigate/test_navigate.py`
- **Code file(s):** `src/renaissance/core/navigate/protocols.py`, `src/renaissance/core/navigate/navigate.py`
