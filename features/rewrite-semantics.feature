Feature: Rewrite semantics
  # FEATURE-REWRITE-SEMANTICS
  # See: docs/user/features/rewrite-semantics.md

  Governs how multiple collected changes are applied to a source file in a single
  rewrite step; defines which combinations are valid and which produce errors.

  Background:
    Given a Python language factory

  # ── Scenario 0 ────────────────────────────────────────────────────────────────
  # Representative examples only. The universal claim — that replacing the same
  # node more than once ALWAYS raises an error regardless of the replacement text
  # — is verified by the Hypothesis test
  # `test_replacing_same_node_twice_always_errors` in
  # features/steps/test-rewrite-semantics.py.
  Scenario Outline: Replacements of the same node produce an error
    Given the source '<source>'
    And the statement '<stmt>' is a node
    When the node is replaced with '<first>'
    And the node is replaced with '<second>'
    Then applying the changes raises an error

    Examples:
      | source     | stmt       | first   | second  | note                                    |
      | a = 1      | a = 1      | A       | B       | assignment — different replacement texts |
      | a = 1      | a = 1      | A       | A       | assignment — identical replacement texts |
      | print(1)   | print(1)   | foo     | bar     | call statement                           |

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
  # Both collection orders must yield the same result: AST structure, not
  # insertion order, determines the output order.
  Scenario Outline: Prepend of ancestor precedes prepend of descendant regardless of collection order
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the <first> is prepended with '<first_text>'
    And the <second> is prepended with '<second_text>'
    Then 'ANC' appears before 'DESC' in the result

    Examples:
      | first      | first_text | second     | second_text | collection order            |
      | ancestor   | ANC        | descendant | DESC        | ancestor collected first    |
      | descendant | DESC       | ancestor   | ANC         | descendant collected first  |

  # ── Scenario 5 ────────────────────────────────────────────────────────────────
  # Both collection orders must yield the same result: AST structure, not
  # insertion order, determines the output order.
  Scenario Outline: Append of descendant precedes append of ancestor regardless of collection order
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the <first> is appended with '<first_text>'
    And the <second> is appended with '<second_text>'
    Then 'DESC' appears before 'ANC' in the result

    Examples:
      | first      | first_text | second     | second_text | collection order            |
      | ancestor   | ANC        | descendant | DESC        | ancestor collected first    |
      | descendant | DESC       | ancestor   | ANC         | descendant collected first  |

  # ── Scenario 6 ────────────────────────────────────────────────────────────────
  Scenario: Append of sibling precedes prepend of next consecutive sibling — append collected first
    Given the source 'a = 1\nb = 2\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the first sibling is appended with 'FIRST'
    And the second sibling is prepended with 'SECOND'
    Then 'FIRST' appears before 'SECOND' in the result

  # ── Scenario 7 ────────────────────────────────────────────────────────────────
  Scenario: Append of sibling precedes prepend of next consecutive sibling — prepend collected first
    Given the source 'a = 1\nb = 2\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the second sibling is prepended with 'SECOND'
    And the first sibling is appended with 'FIRST'
    Then 'FIRST' appears before 'SECOND' in the result
