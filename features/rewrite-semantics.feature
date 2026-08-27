Feature: Rewrite semantics
  # FEATURE-REWRITE-SEMANTICS
  # See: docs/user/features/rewrite-semantics.md
  # See also: docs/glossary.md — definitions of operators, AST terms, and
  #           collection of changes.

  Use this feature to understand how the tool applies multiple edits — insertions
  and replacements — to a source file in one pass, and which combinations of edits
  are valid or produce errors.

  The rewrite semantics are language-agnostic and apply to every language supported
  by the tool.

  Background:
    Given a Python language factory

  # Python is chosen only to make the scenarios concrete and runnable; the rules
  # described here hold for all supported languages.

  # ── Format: Gherkin / BDD ────────────────────────────────────────────────────────
  # These scenarios are written in Gherkin (https://cucumber.io/docs/gherkin/), the
  # notation used by behaviour-driven development (BDD,
  # https://cucumber.io/docs/bdd/).
  #
  # Scenario         — one concrete, self-contained example of a rule.
  # Scenario Outline — a parameterised template expanded by an Examples table.
  #                    Each row produces one test case; '<column>' placeholders in
  #                    the steps are substituted with the row values at run time.
  #                    The last column ('note', 'combination', or 'collection order')
  #                    labels the case for human readers and is not used in any step.

  # ── Operators ────────────────────────────────────────────────────────────────────
  # Four operators can be applied to an AST node (full definitions: docs/glossary.md):
  #   replace(text)           — substitute the node's source text with 'text'.
  #   prepend(text)           — insert 'text' immediately before the node.
  #   append(text)            — insert 'text' immediately after the node.
  #   surround(before, after) — insert 'before' before and 'after' after the node.

  # ── Sentinel tokens ──────────────────────────────────────────────────────────────
  # All-caps tokens are literal strings used only to verify output ordering;
  # they never appear in the source code under test.
  # Self-describing tokens: the name describes the expected position in the output.
  #   PREPEND, APPEND, REPLACEMENT
  #   BEFORE, AFTER
  #   SURROUND_BEFORE, SURROUND_AFTER
  #   ANC, DESC, ANC_BEF, ANC_AFT, DESC_BEF, DESC_AFT
  #   FIRST, SECOND, BEFORE1, AFTER1, BEFORE2, AFTER2
  # Special tokens:
  #   DONT_CARE — a surround argument not at the boundary under test;
  #               its value is not part of the assertion.
  #   DOMINATED — used only in dominance scenarios to prove a dominated change was
  #               NOT applied: it must not appear in the source or in any dominating
  #               replacement text, so any occurrence in the output is a test failure.

  # ── Collection order ─────────────────────────────────────────────────────────────
  # 'Collection order' is the sequence in which changes are registered before the
  # rewrite is committed (see docs/glossary.md — Collection of changes).
  # Collection order is significant ONLY when the same operator is applied multiple
  # times to the same node (see Group: Single operator — same node):
  #   • prepend  — applied in collection order (first collected = leftmost).
  #   • append   — applied in reversed collection order (first collected = rightmost).
  #   • surround — before texts in collection order; after texts in reversed order.
  # In all other situations the output order is determined by AST structure, not
  # by collection order.

  # ── Representative examples ──────────────────────────────────────────────────────
  # Representative examples only. The universal claim — e.g., that replacing the same
  # node more than once ALWAYS raises an error regardless of the replacement text
  # — is verified by Hypothesis tests.
  #
  # Scenario |  test
  # Equal    | `test_replacing_same_node_twice_always_errors` in test/syntax_tree/test_rewrite_semantics_properties.py.

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Error cases
  # Combinations that cannot produce a valid result are rejected immediately.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Equal — node ────────────────────────────────────────────────────────────────
  Scenario Outline: Replacements of the same node produce an error
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is replaced with '<first>'
    And the node is replaced with '<second>'
    Then applying the changes raises an error

    Examples:
      | first   | second  | note                           |
      | A       | B       | different replacement texts    |
      | A       | A       | identical replacement texts    |
      | ""      | ""      | identical removal (empty text) |

  # ── Scenario Equal — sibling range ────────────────────────────────────────────────
  Scenario Outline: Replacements of the same sibling range produce an error
    Given the source 'a = 1\nb = 2\nc = 3\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the first and second siblings are replaced with '<first>'
    And the first and second siblings are replaced with '<second>'
    Then applying the changes raises an error

    Examples:
      | first   | second  | note                                        |
      | A       | B       | different replacement texts                 |
      | A       | A       | identical replacement texts                 |
      | ""      | ""      | identical removal (empty text)              |

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
  # At the text level all share the same principle: a replacement with a
  # larger text range dominates any replacement with a smaller text range that
  # is fully contained within it.
  # From an AST point of view this principle manifests in two ways:
  #   Ancestor dominance: a replacement on an ancestor node suppresses changes on
  #                       its descendants as the ancestor's text range contains the
  #                       descendant's text range.
  #   Range dominance:    a replacement on a sibling range suppresses replacements
  #                       on any proper subrange (including a single sibling) that
  #                       is fully contained within the larger range.
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Dominance — ancestor ────────────────────────────────────────────────
  # 'DOMINATED' is the dominated change text; see Sentinel tokens in the preamble.
  Scenario Outline: Dominated change is not applied
    Given the source 'a = 1'
    And the statement 'a = 1' is the parent node
    And the first leaf of the parent is the child node
    When the parent node is replaced with 'x = 99'
    And the child node is <changed>
    Then the result contains 'x = 99'
    But the result does not contain 'DOMINATED'

    Examples:
      | changed                                     |
      | replaced with 'DOMINATED'                   |
      | appended with 'DOMINATED'                   |
      | prepended with 'DOMINATED'                  |
      | surrounded with 'DOMINATED' and 'DOMINATED' |

  # ── Scenario Range Dominance — subrange ─────────────────────────────────────────────
  # Range [sib1, sib2, sib3] dominates the subrange [sib1, sib2].
  # 'DOMINATED' is the dominated change text; see Sentinel tokens in the preamble.
  Scenario Outline: Sibling range dominates a proper subrange regardless of collection order
    Given the source 'a = 1\nb = 2\nc = 3\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    And the statement 'c = 3' is the third sibling
    When the <first_op>
    And the <second_op>
    Then the result contains 'RANGE'
    But the result does not contain 'DOMINATED'

    Examples:
      | first_op                                                        | second_op                                                     | collection order             |
      | first, second and third siblings are replaced with 'RANGE'      | first and second siblings are replaced with 'DOMINATED'       | range collected first        |
      | first and second siblings are replaced with 'DOMINATED'         | first, second and third siblings are replaced with 'RANGE'    | subrange collected first     |

  # ── Scenario Range Dominance — single sibling ────────────────────────────────────────
  # Range [sib1, sib2] dominates the single sibling [sib2].
  # 'DOMINATED' is the dominated change text; see Sentinel tokens in the preamble.
  Scenario Outline: Sibling range dominates a single contained sibling regardless of collection order
    Given the source 'a = 1\nb = 2\nc = 3\n'
    And the statement 'a = 1' is the first sibling
    And the statement 'b = 2' is the second sibling
    When the <first_op>
    And the <second_op>
    Then the result contains 'RANGE'
    But the result does not contain 'DOMINATED'

    Examples:
      | first_op                                            | second_op                                             | collection order                |
      | first and second siblings are replaced with 'RANGE' | second sibling is replaced with 'DOMINATED'           | range collected first           |
      | second sibling is replaced with 'DOMINATED'         | first and second siblings are replaced with 'RANGE'   | single sibling collected first  |

  # ════════════════════════════════════════════════════════════════════════════════
  # Group: Single operator — same node
  # Ordering when the same operator is applied to the same node more than once.
  # Collection order IS significant here — see the preamble for the per-operator rules.
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
  # Collection order is NOT significant here.
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
  # Group: Cross-operator — same node
  # Regardless of collection order, the output always follows the structural order:
  #   prepend → surround-before → node → surround-after → append
  # When the node is replaced, the replacement text occupies the node position:
  #   prepend → surround-before → replacement → surround-after → append
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

  # ── Scenario Replace + Prepend — same node ────────────────────────────────────────
  # Prepend text appears before the replacement text, regardless of collection order.
  Scenario: Prepend appears before replacement of the same node — prepend collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is prepended with 'PREPEND'
    And the node is replaced with 'REPLACEMENT'
    Then 'PREPEND' appears before 'REPLACEMENT' in the result

  Scenario: Prepend appears before replacement of the same node — replace collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is replaced with 'REPLACEMENT'
    And the node is prepended with 'PREPEND'
    Then 'PREPEND' appears before 'REPLACEMENT' in the result

  # ── Scenario Replace + Append — same node ─────────────────────────────────────────
  # Replacement text appears before append text, regardless of collection order.
  Scenario: Replacement appears before append of the same node — replace collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is replaced with 'REPLACEMENT'
    And the node is appended with 'APPEND'
    Then 'REPLACEMENT' appears before 'APPEND' in the result

  Scenario: Replacement appears before append of the same node — append collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is appended with 'APPEND'
    And the node is replaced with 'REPLACEMENT'
    Then 'REPLACEMENT' appears before 'APPEND' in the result

  # ── Scenario Replace + Surround — same node ───────────────────────────────────────
  # Surround before text appears before the replacement; replacement appears before
  # surround after text, regardless of collection order.
  Scenario: Surround wraps replacement of the same node — replace collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is replaced with 'REPLACEMENT'
    And the node is surrounded with 'SURROUND_BEFORE' and 'SURROUND_AFTER'
    Then 'SURROUND_BEFORE' appears before 'REPLACEMENT' in the result
    And 'REPLACEMENT' appears before 'SURROUND_AFTER' in the result

  Scenario: Surround wraps replacement of the same node — surround collected first
    Given the source 'a = 1'
    And the statement 'a = 1' is a node
    When the node is surrounded with 'SURROUND_BEFORE' and 'SURROUND_AFTER'
    And the node is replaced with 'REPLACEMENT'
    Then 'SURROUND_BEFORE' appears before 'REPLACEMENT' in the result
    And 'REPLACEMENT' appears before 'SURROUND_AFTER' in the result

# ════════════════════════════════════════════════════════════════════════════════
  # Group: Cross-operator — different nodes sharing a text location
  # Nodes are in adjacent sibling relationship.
  # The operation on a sibling always places its text before the operation on the next
  # consecutive sibling at their shared text boundary, regardless of collection order.
  # (append vs. prepend/surround-before; surround-after vs. prepend/surround-before)
  #
  # C++ is used here: in 'a=1;b=2;', sib1's end location is equal to sib2's start location —
  # a genuinely shared byte boundary. 
  # In Python adjacent siblings never share a text location.
  # For example, statements in python are always separated by either '\n' or ';' 
  # and these separators are not part of the statement.
  #
  # 'AFTER' is the canonical token for the text at the end of sib1 (append argument,
  # or second argument of surround). 'BEFORE' is the canonical token for the text at
  # the start of sib2 (prepend argument, or first argument of surround).
  # ════════════════════════════════════════════════════════════════════════════════

  # ── Scenario Siblings — shared text boundary, sib1 collected first ────────────────
  Scenario Outline: Operation on first sibling precedes operation on second sibling — first sibling collected first
    Given a C++ language factory
    And the source 'a=1;b=2;'
    And the statement 'a=1' is the first sibling
    And the statement 'b=2' is the second sibling
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
    Given a C++ language factory
    And the source 'a=1;b=2;'
    And the statement 'a=1' is the first sibling
    And the statement 'b=2' is the second sibling
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
  # Group: Cross-operator — different nodes sharing a text location
  # Nodes are in ancestor - descendant relationship.
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
