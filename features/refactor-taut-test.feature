Feature: taut migration
  Scenario: remove import
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'import TAUT' exits within that AST
    When that node is removed
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is removed

  Scenario: replace taut
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'class $a(TAUT.TestCase): $$bb' exits within that AST
    When that node is replaced by 'class $a(unittest.TestCase): $$bb'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text

  Scenario: remove decorator
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors

  Scenario: replace import
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'self.import_and_verify_module('EMRWxTL')' exits within that AST
    When that node is replaced by 'import EMRWxTL\nself.assertIsNotNone(EMRWxTL)'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text

