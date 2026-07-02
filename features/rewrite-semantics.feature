Feature: Rewrite semantics
  # FEATURE-REWRITE-SEMANTICS
  # See: docs/user/features/rewrite-semantics.md

  Governs how multiple collected changes are applied to a source file in a single
  rewrite step; defines which combinations are valid and which produce errors.

  Background:
    Given a Python language factory

  # Representative examples only. The universal claim — e.g., that replacing the same
  # node more than once ALWAYS raises an error regardless of the replacement text
  # — is verified by Hypothesis tests
  # 
  # Scenario |  test
  # Equal    | `test_replacing_same_node_twice_always_errors` in test/syntax_tree/test_rewrite_semantics_properties.py.
  #
  # Sentinel tokens used across scenarios:
  # 'DONT_CARE' marks a surround argument that is not at the boundary under test
  #             and is not part of the assertion.

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Error cases
  # Combinations that cannot produce a valid result are rejected immediately.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Equal ────────────────────────────────────────────────────────────────
  Scenario Outline: Replacements of the same node produce an error
    Given the source '<source>'
    And the statement '<stmt>' is a node
    When the node is replaced with '<first>'
    And the node is replaced with '<second>'
    Then applying the changes raises an error

    Examples:
      | source     | stmt       | first   | second  | note                                        |
      | a = 1      | a = 1      | A       | B       | assignment — different replacement texts    |
      | a = 1      | a = 1      | A       | A       | assignment — identical replacement texts    |
      | a = 1      | a = 1      | ""      | ""      | assignment — identical removal (empty text) |
      | print(1)   | print(1)   | foo     | bar     | call statement                              |

  # ── Scenario Overlap ──────────────────────────────────────────────────────────────
  Scenario Outline: Overlapping replacements produce an error
    Given the source 'a = 1\nb = 2\nc = 3\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    And the statement 'c = 3' is the third sibling
    When the first and second siblings are replaced with '<first>'
    And the second and third siblings are replaced with '<second>'
    Then applying the changes raises an error

    Examples:
      | first   | second  | note                             |
      | A       | B       | different replacement texts      |
      | A       | A       | identical replacement texts      |
      | ""      | ""      | overlapping removal (empty text) |

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Dominance and suppression
  # A change on an ancestor node suppresses any covered changes on its descendants.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Cover ────────────────────────────────────────────────────────────────
  # 'COVERED' is a sentinel value: it must not appear in the source ('a = 1') or in
  # the replacement text ('x = 99'). Any occurrence of 'COVERED' in the result
  # therefore means the covered change was wrongly applied.
  Scenario Outline: Covered change is not applied
    Given the source 'a = 1'
    And the statement 'a = 1' is the parent node
    And the first leaf of the parent is the child node
    When the parent node is replaced with 'x = 99'
    And the child node is <changed>
    Then the result contains 'x = 99'
    But the result does not contain 'COVERED'

    Examples:
      | changed                                 |
      | replaced with 'COVERED'                 |
      | appended with 'COVERED'                 |
      | prepended with 'COVERED'                |
      | surrounded with 'COVERED' and 'COVERED' |

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Single operator — same node
  # Ordering when the same operator is applied to the same node more than once.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Prepends — same node ────────────────────────────────────────────────
  # Multiple prepends on the same node are applied in collection order.
  Scenario: Prepends of same node are applied in order of collection.
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is prepended with 'FIRST'
    And the node is prepended with 'SECOND'
    Then 'FIRST' appears before 'SECOND' in the result

  # ── Scenario Appends — same node ─────────────────────────────────────────────────
  # Multiple appends on the same node are applied in reversed collection order.
  Scenario: Appends of same node are applied in reversed order of collection.
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is appended with 'FIRST'
    And the node is appended with 'SECOND'
    Then 'SECOND' appears before 'FIRST' in the result

  # ── Scenario Surrounds — same node ───────────────────────────────────────────────
  # Before texts appear in collection order; after texts in reversed collection order.
  Scenario: Surrounds of same node: before texts in collection order, after texts in reversed collection order
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is surrounded with 'BEFORE1' and 'AFTER1'
    And the node is surrounded with 'BEFORE2' and 'AFTER2'
    Then 'BEFORE1' appears before 'BEFORE2' in the result
    And 'AFTER2' appears before 'AFTER1' in the result

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Single operator — different nodes sharing a text location
  # AST structure determines order when ancestor
  # and descendant nodes share a start or end text position — not collection order.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Prepends — different nodes, shared start location ───────────────────
  # Both collection orders must yield the same result: 
  # AST structure determines the order - not collection order.
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

  # ── Scenario Appends — different nodes, shared end location ──────────────────────
  # Both collection orders must yield the same result: 
  # AST structure determines the order - not collection order.
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

  # ── Scenario Surrounds — different nodes, shared start location ──────────────────
  # Both collection orders must yield the same result: 
  # AST structure determines the order - not collection order.
  Scenario Outline: Surround of ancestor precedes surround of descendant at shared start location regardless of collection order
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the <first> is surrounded with '<first_before>' and '<first_after>'
    And the <second> is surrounded with '<second_before>' and '<second_after>'
    Then 'ANC_BEF' appears before 'DESC_BEF' in the result

    Examples:
      | first      | first_before | first_after | second     | second_before | second_after | collection order           |
      | ancestor   | ANC_BEF      | DONT_CARE   | descendant | DESC_BEF      | DONT_CARE    | ancestor collected first   |
      | descendant | DESC_BEF     | DONT_CARE   | ancestor   | ANC_BEF       | DONT_CARE    | descendant collected first |

  # ── Scenario Surrounds — different nodes, shared end location ────────────────────
  # Both collection orders must yield the same result: AST structure, not
  # insertion order, determines the output order of the after texts.
  Scenario Outline: Surround of descendant precedes surround of ancestor at shared end location regardless of collection order
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the <first> is surrounded with '<first_before>' and '<first_after>'
    And the <second> is surrounded with '<second_before>' and '<second_after>'
    Then 'DESC_AFT' appears before 'ANC_AFT' in the result

    Examples:
      | first      | first_before | first_after | second     | second_before | second_after | collection order           |
      | ancestor   | DONT_CARE    | ANC_AFT     | descendant | DONT_CARE     | DESC_AFT     | ancestor collected first   |
      | descendant | DONT_CARE    | DESC_AFT    | ancestor   | DONT_CARE     | ANC_AFT      | descendant collected first |

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Adjacent siblings — shared text boundary
  # The operation on a sibling always places its text before the operation on the next
  # consecutive sibling at their shared text boundary, regardless of collection order.
  # (append vs. prepend/surround-before; surround-after vs. prepend/surround-before)
  #
  # 'AFTER' is the canonical token for the text at the end of sib1 (append argument,
  # or second argument of surround). 'BEFORE' is the canonical token for the text at
  # the start of sib2 (prepend argument, or first argument of surround).
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Siblings — shared text boundary, sib1 collected first ────────────────
  Scenario Outline: Operation on first sibling precedes operation on second sibling — first sibling collected first
    Given the source 'a = 1\nb = 2\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the first sibling is <sib1_op>
    And the second sibling is <sib2_op>
    Then 'AFTER' appears before 'BEFORE' in the result

    Examples:
      | sib1_op                                    | sib2_op                                    | combination                      |
      | appended with 'AFTER'                      | prepended with 'BEFORE'                    | append + prepend                 |
      | surrounded with 'DONT_CARE' and 'AFTER'    | prepended with 'BEFORE'                    | surround-after + prepend         |
      | appended with 'AFTER'                      | surrounded with 'BEFORE' and 'DONT_CARE'   | append + surround-before         |
      | surrounded with 'DONT_CARE' and 'AFTER'    | surrounded with 'BEFORE' and 'DONT_CARE'   | surround-after + surround-before |

  # ── Scenario Siblings — shared text boundary, sib2 collected first ────────────────
  Scenario Outline: Operation on first sibling precedes operation on second sibling — second sibling collected first
    Given the source 'a = 1\nb = 2\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the second sibling is <sib2_op>
    And the first sibling is <sib1_op>
    Then 'AFTER' appears before 'BEFORE' in the result

    Examples:
      | sib1_op                                    | sib2_op                                    | combination                      |
      | appended with 'AFTER'                      | prepended with 'BEFORE'                    | append + prepend                 |
      | surrounded with 'DONT_CARE' and 'AFTER'    | prepended with 'BEFORE'                    | surround-after + prepend         |
      | appended with 'AFTER'                      | surrounded with 'BEFORE' and 'DONT_CARE'   | append + surround-before         |
      | surrounded with 'DONT_CARE' and 'AFTER'    | surrounded with 'BEFORE' and 'DONT_CARE'   | surround-after + surround-before |

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Cross-operator — same node
  # When different operators target the same node, surround is always closer to
  # the node than prepend or append, regardless of collection order.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Prepend + Surround — same node ───────────────────────────────────────
  # Surround is always closer to the AST node than prepend, regardless of collection order.
  Scenario: Prepend is outside surround of the same node — prepend collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is prepended with 'FIRST'
    And the node is surrounded with 'BEFORE' and 'DONT_CARE'
    Then 'FIRST' appears before 'BEFORE' in the result

  Scenario: Prepend is outside surround of the same node — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is surrounded with 'BEFORE' and 'DONT_CARE'
    And the node is prepended with 'FIRST'
    Then 'FIRST' appears before 'BEFORE' in the result

  # ── Scenario Append + Surround — same node ────────────────────────────────────────
  # Surround is always closer to the AST node than append, regardless of collection order.
  Scenario: Append is outside surround of the same node — append collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is appended with 'FIRST'
    And the node is surrounded with 'DONT_CARE' and 'AFTER'
    Then 'AFTER' appears before 'FIRST' in the result

  Scenario: Append is outside surround of the same node — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is surrounded with 'DONT_CARE' and 'AFTER'
    And the node is appended with 'FIRST'
    Then 'AFTER' appears before 'FIRST' in the result

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Cross-operator — different nodes sharing a text location
  # Insertions on a descendant node are always closer to that node than insertions
  # on an ancestor node, regardless of collection order.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Surround (ancestor) + Prepend (descendant) — shared start location ───
  # Descendant's prepend is always closer to the descendant node than the ancestor's
  # surround before text, regardless of collection order.
  Scenario: Prepend of descendant is inside surround of ancestor at shared start location — prepend collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the descendant is prepended with 'DESC_PRE'
    And the ancestor is surrounded with 'ANC_BEF' and 'DONT_CARE'
    Then 'ANC_BEF' appears before 'DESC_PRE' in the result

  Scenario: Prepend of descendant is inside surround of ancestor at shared start location — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the ancestor is surrounded with 'ANC_BEF' and 'DONT_CARE'
    And the descendant is prepended with 'DESC_PRE'
    Then 'ANC_BEF' appears before 'DESC_PRE' in the result

  # ── Scenario Surround (ancestor) + Append (descendant) — shared end location ───────
  # Descendant's append is always closer to the descendant node than the ancestor's
  # surround after text, regardless of collection order.
  Scenario: Append of descendant is inside surround of ancestor at shared end location — append collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the descendant is appended with 'DESC_APP'
    And the ancestor is surrounded with 'DONT_CARE' and 'ANC_AFT'
    Then 'DESC_APP' appears before 'ANC_AFT' in the result

  Scenario: Append of descendant is inside surround of ancestor at shared end location — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the ancestor is surrounded with 'DONT_CARE' and 'ANC_AFT'
    And the descendant is appended with 'DESC_APP'
    Then 'DESC_APP' appears before 'ANC_AFT' in the result

  # ── Scenario Surround (descendant) + Prepend (ancestor) — shared start location ───
  # Descendant's surround before text is always closer to the descendant node than
  # the ancestor's prepend, regardless of collection order.
  Scenario: Surround of descendant is inside prepend of ancestor at shared start location — prepend collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the ancestor is prepended with 'ANC_PRE'
    And the descendant is surrounded with 'DESC_BEF' and 'DONT_CARE'
    Then 'ANC_PRE' appears before 'DESC_BEF' in the result

  Scenario: Surround of descendant is inside prepend of ancestor at shared start location — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the first leaf of the ancestor is the descendant node
    When the descendant is surrounded with 'DESC_BEF' and 'DONT_CARE'
    And the ancestor is prepended with 'ANC_PRE'
    Then 'ANC_PRE' appears before 'DESC_BEF' in the result

  # ── Scenario Surround (descendant) + Append (ancestor) — shared end location ───────
  # Descendant's surround after text is always closer to the descendant node than
  # the ancestor's append, regardless of collection order.
  Scenario: Surround of descendant is inside append of ancestor at shared end location — append collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the ancestor is appended with 'ANC_APP'
    And the descendant is surrounded with 'DONT_CARE' and 'DESC_AFT'
    Then 'DESC_AFT' appears before 'ANC_APP' in the result

  Scenario: Surround of descendant is inside append of ancestor at shared end location — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is the ancestor node
    And the last leaf of the ancestor is the descendant node
    When the descendant is surrounded with 'DONT_CARE' and 'DESC_AFT'
    And the ancestor is appended with 'ANC_APP'
    Then 'DESC_AFT' appears before 'ANC_APP' in the result
