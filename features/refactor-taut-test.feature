Feature: taut migration
  Scenario: remove import
    Given 'targets/taut/taut_test.py' file
    And it contains 'import TAUT'
    And an AST extracted from that source file without errors
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should not contain 'import TAUT'

  Scenario: replace taut
    Given 'targets/taut/taut_test.py' file
    And it contains 'class TestImport(TAUT.TestCase):'
    And an AST extracted from that source file without errors
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'class TestImport(unittest.TestCase):'

  Scenario: replace import
    Given 'targets/taut/taut_test.py' file
    And it contains 'self.import_and_verify_module('ABCDxTL')'
    And an AST extracted from that source file without errors
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'import ABCDxTL\r\n        self.assertIsNotNone(ABCDxTL)'

  Scenario: remove decorator
    Given 'targets/taut/taut_test.py' file
    And it contains '@TAUT.log_stub'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should not contain '@TAUT.log_stub'

  Scenario: replace TestDoubles
    Given 'targets/taut/taut_test.py' file
    And it contains 'with TAUT.TestDoubles(abcdxtl=FakeABCDxTL(None)):'
    And it contains 'log = TAUT.Logger()'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'fake_abcdxtl = FakeABCDxTL(None)'
    And it should not contain 'log = TAUT.Logger()'
    And it should contain 'test_log = fake_abcdxtl.create_test_log(test_log_id)'
    And it should contain 'test_log, version_mismatch = fake_abcdxtl.retrieve_test_log(file_id, test_log_id, file_name)'
    And it should contain 'fake_abcdxtl.store_test_log(file_id, test_log)'

  Scenario: convert setUp
    Given 'targets/taut/taut_test.py' file
    And it contains 'def setUp(self):'
    And it contains 'self.doubles'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'self.patches'
    And it should contain 'p.start()'
    And it should not contain 'self.doubles'

  Scenario: convert tearDown
    Given 'targets/taut/taut_test.py' file
    And it contains 'def tearDown(self):'
    And it contains 'self.tds'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'self.patches'
    And it should contain 'p.stop()'
    And it should not contain 'self.tds'

  Scenario: convert setUpCommon
    Given 'targets/taut/taut_test.py' file
    And it contains 'def setUpCommon(self):'
    And it contains 'self.tds'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'def setUpCommon(self):'
    And it should contain 'self.patchers'
    And it should contain 'p.start()'
    And it should not contain 'self.tds'

  Scenario: convert tearDownCommon
    Given 'targets/taut/taut_test.py' file
    And it contains 'def tearDownCommon(self):'
    And it contains 'self.tds'
    When I convert taut to unittest
    Then AST extracted from that conversion should without errors
    And it should contain 'def tearDownCommon(self):'
    And it should contain 'self.patchers'
    And it should contain 'p.stop()'
    And it should not contain 'self.tds'
