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
    And node '@TAUT.log_stub\ndef $a($$bb): $$cc' exits within that AST

  Scenario: replace import
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'self.import_and_verify_module('EMRWxTL')' exits within that AST
    When that node is replaced by 'import EMRWxTL\nself.assertIsNotNone(EMRWxTL)'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text

  Scenario: replace TestDoubles
    Given 'python' programming language
    And 'targets/taut/taut_test.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)): $$aa' exits within that AST
    When that node is replaced by '$$aa'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text
    Given node 'log = TAUT.Logger()' exits within that AST
    When that node is removed
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is removed
    Given node 'emrwxtl.$a($$bb)' exits within that AST
    When that node is replaced by 'fake_emrwxtl.$a($$bb)'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text
    Given node '$c = emrwxtl.$a($$bb)' exits within that AST
    When that node is replaced by '$c = fake_emrwxtl.$a($$bb)'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text
