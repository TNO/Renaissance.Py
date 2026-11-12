<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core feature ↔ test mappings

## 1. Pattern matching

- **Feature:** [Pattern matching](../../user/features/pattern_matching.md)
- **Concepts:** [Pattern](../../user/core/pattern.md)
- **Code modules:** [Core pattern](../modules/core/pattern.md)
- **Test file(s):**
    - `test/syntax_tree/test_match_finder.py`
    - `test/syntax_tree/test_match_finder_multi_assignments.py`
    - `test/syntax_tree/test_match_tree.py`
    - `test/syntax_tree/test_match_dict.py`
    - `test/syntax_tree/test_pattern_match.py`
    - `test/unit/core/pattern/test_pattern_kind.py`
    - `test/python/ast/test_python_matcher.py`
    - `test/python/ast/test_python_pattern_type_parameters.py`
    - `test/c_cpp/test_c_match_finder.py`
- **Code file(s):** `src/renaissance/syntax_tree/match_finder.py`, `src/renaissance/core/pattern/pattern_kind.py`,
  `src/renaissance/core/pattern/placeholders.py`, `src/renaissance/integrations/python/ast/factory.py`

## 2. Rewrite semantics

- **Feature:** [Rewrite semantics](../../user/features/rewrite_semantics.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite_semantics.md)
- **Test modules:** [Rewrite semantics test module](../../developer/modules/rewrite_semantics.md)
- **BDD feature file:** `features/rewrite_semantics.feature`
- **BDD steps:** `features/steps/test_rewrite_semantics.py`
- **Test file(s):**
    - `test/common/test_rewriter.py`
    - `test/syntax_tree/test_ast_rewriter.py`
    - `test/syntax_tree/test_rewrite_semantics_properties.py`
- **Code files:** `src/renaissance/common/rewriter.py`, `src/renaissance/syntax_tree/ast_rewriter.py`

## 3. Type parameter modernization

- **Feature:** [Type parameter modernization](../../user/features/type_parameter_modernization.md)
- **Concepts:** [Rewrite semantics](../../user/concepts/rewrite_semantics.md)
- **Code modules:** [Refactoring recipes](../../developer/modules/recipes.md)
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
    - `test/python/ast/test_cst_utils.py`
    - `test/utils/test_import_resolution.py`
    - `test/rejuvenation/test_migration_type_recipes.py`
- **Code file(s):** `src/renaissance/recipes/type_parameter_check.py`, `src/renaissance/recipes/type_parameter_rules.py`,
  `src/renaissance/recipes/type_parameter_declarations.py`, `src/renaissance/recipes/type_parameter_localization.py`,
  `src/renaissance/recipes/type_parameter_uses.py`,
  `src/renaissance/recipes/step_runner.py`,
  `src/renaissance/recipes/python_refactoring.py`,
  `src/renaissance/utils/import_resolution.py`, `src/renaissance/integrations/python/ast/cst_utils.py`,
  `src/rejuvenation/migration_type_recipes.py`

## 4. Navigation

- **Feature:** [Navigation](../../user/features/navigation.md)
- **Concepts:** [Navigate](../../user/core/navigate.md)
- **Code modules:** [Core navigate](../modules/core/navigate.md)
- **Test file(s):**
    - `test/unit/core/navigate/test_navigate.py`
- **Code file(s):** `src/renaissance/core/navigate/protocols.py`, `src/renaissance/core/navigate/navigate.py`
