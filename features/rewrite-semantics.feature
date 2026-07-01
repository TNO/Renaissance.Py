Feature: Rewrite semantics
  # FEATURE-REWRITE-SEMANTICS
  # See: docs/user/features/rewrite-semantics.md

  Governs how multiple collected changes are applied to a source file in a single
  rewrite step; defines which combinations are valid and which produce errors.

  Background:
    Given a Python language factory

  # ── Scenario 0 ────────────────────────────────────────────────────────────────
  Scenario: Replacements of the same node produce an error
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is replaced with 'A'
    And the node is replaced with 'B'
    Then applying the changes raises an error

  # ── Scenario 1 ────────────────────────────────────────────────────────────────
  Scenario: Covered replacements are not applied
    Given the source 'a = 1'
    And the statement 'a = 1' is the parent node
    And the first leaf of the parent is the child node
    When the parent node is replaced with 'x = 99'
    And the child node is replaced with 'COVERED'
    Then the result contains 'x = 99'
    And the result does not contain 'COVERED'

  # ── Scenario 2 ────────────────────────────────────────────────────────────────
  Scenario: Covered inserts are not applied
    Given the source 'a = 1'
    And the statement 'a = 1' is the parent node
    And the first leaf of the parent is the child node
    When the parent node is replaced with 'x = 99'
    And the child node is prepended with 'COVERED'
    Then the result contains 'x = 99'
    And the result does not contain 'COVERED'

  # ── Scenario 3 ────────────────────────────────────────────────────────────────
  Scenario: Overlapping replacements produce an error
    Given the source 'a = 1\nb = 2\nc = 3\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    And the statement 'c = 3' is the third sibling
    When the first and second siblings are replaced with 'REPLACED'
    And the second and third siblings are replaced with 'REPLACED'
    Then applying the changes raises an error

  # ── Scenario 4 ────────────────────────────────────────────────────────────────
  Scenario: Prepend of ancestor precedes prepend of descendant at the same text location
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the ancestor is prepended with 'ANC'
    And the descendant is prepended with 'DESC'
    Then 'ANC' appears before 'DESC' in the result

  # ── Scenario 5 ────────────────────────────────────────────────────────────────
  Scenario: Append of descendant precedes append of ancestor at the same text location
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the ancestor is appended with 'ANC'
    And the descendant is appended with 'DESC'
    Then 'DESC' appears before 'ANC' in the result

  # ── Scenario 6 ────────────────────────────────────────────────────────────────
  Scenario: Append of sibling precedes prepend of next consecutive sibling
    Given the source 'a = 1\nb = 2\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the first sibling is appended with 'FIRST'
    And the second sibling is prepended with 'SECOND'
    Then 'FIRST' appears before 'SECOND' in the result
