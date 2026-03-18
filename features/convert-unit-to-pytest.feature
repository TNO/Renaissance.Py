Feature: Convert unittest to pytest
  In order to create modern pythton project
  As a Developer
  I want a consistent set of unit test expressing specification of code behavior
  Scenario: convert unittest to pytest
    Given 'targets/pyunit_test_example.py' file
    And it contains 'import unittest'
    And it contains 'from unittest import TestCase'
    And it contains 'assert '
    And it contains 'self.assertEqual(a,5)'
    And it contains 'self.assertEqual(55,b)'
    And it contains '@unittest.skip'
    And it contains '@parameterized.expand'
    And it contains 'class FindDescendantMatchTest(unittest.TestCase):'
    And an AST extracted from that source file without errors
    When I convert it to pytest
    Then AST extracted from that conversion should without errors
    And it should not contain 'import unittest'
    And it should not contain 'assert '
    And it should not contain 'assertEqual(a,5)'
    And it should not contain 'assertEqual(55,b)'
    And it should not contain '@unittest.skip'
    And it should not contain '@parameterized.expand'
    And it should not contain 'class FindDescendantMatchTest(unittest.TestCase):'
    And it should not contain 'import unittest'
    And it contains 'import pytest'
    And it contains 'assert_that '
    And it contains 'assert_that(a,is_(5))'
    And it contains 'assertEqual(b,is_(55))'
    And it contains '@pytest.mark.skip'
    And it contains '@pytest.mark.parameterized'
    And it contains 'class TestFindDescendantMatch:'
