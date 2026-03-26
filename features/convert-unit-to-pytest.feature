Feature: Convert unittest to pytest
  In order to create modern pythton project
  As a Developer
  I want a consistent set of unit test expressing specification of code behavior
  Scenario: convert unittest to pytest
    Given 'targets/pyunit_test_example.py' file
    And it contains 'import unittest'
    And it contains 'from unittest import TestCase'
    And it contains 'assert '
    And it contains 'self.assertEqual'
    And it contains 'print'
    And it contains '@unittest.skip'
    And it contains '@parameterized.expand'
    And it contains 'class FindMatchTest(unittest.TestCase):'
    And it contains 'def test_it_has_elements():'
    And it contains 'assert 0 == count, "count = " + str(count)'
    And an AST extracted from that source file without errors
    When I convert it to pytest
    Then AST extracted from that conversion should without errors
    And it should not contain 'import unittest'
    And it should not contain 'assert 0 == count, "count = " + str(count)'
    And it should not contain 'assertEqual(a,5)'
    And it should not contain 'assertEqual(55,b)'
    And it should not contain '@unittest.skip'
    And it should not contain '@parameterized.expand'
    And it should not contain 'class FindDescendantMatchTest(unittest.TestCase):'

    And it should contain 'import pytest'
    And it should contain 'assert_that(results, has_length(0), f"length of results = {len(results)}")'
    And it should contain 'assert_that(self.a, is_(5))'
    And it should contain 'assert_that(self.b, is_(55))'
    And it should contain '@pytest.mark.skip'
    And it should contain '@pytest.mark.parametrize("_, factory",Factories.factories)'

    And it should contain 'class TestFindMatch:'
