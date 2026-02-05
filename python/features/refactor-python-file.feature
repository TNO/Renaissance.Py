Feature: Ast based changes
  In order to get started on the system test
  As a Developer
  I want a working example of how system test looks like

  Scenario: python code
    Given 'python' programming language
    And 'examples/demo.py' file written in that programming language
    And an AST extracted from that source file without errors
    And node 'some_old_fun' exits within that AST
    And a sequence of descendant nodes of that node
    When that node is replaced by 'def my_awesome_fun(): pass'
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text
    And all rewrites on that sequence of descendant nodes are not performed or hidden
