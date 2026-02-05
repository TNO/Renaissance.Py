Feature: Ast based changes
  Scenario: python code
    Given 'python' programming language
    And	a source file written in that programming language
    And	an AST extracted from that source file without errors
    And	a node of that AST
    And	a sequence of descendant nodes of that node
    When that node is replaced by a text
    And rewrites replace is performed on that sequence of descendant nodes
    Then in the modified source file that node is replaced by the given text
    And all rewrites on that sequence of descendant nodes are not performed / hidden