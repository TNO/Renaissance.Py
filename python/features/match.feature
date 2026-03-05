#Feature: AST-based pattern matching
#
#Scenario Outline: match is insensitive to comment
#   Given a piece of code
#     And a kind of <change>
#    When applying that <change> to the code
#    Then the original code and changed code match
#
# Examples: Change
#   | change         |
#   | add comment    |
#   | remove comment |
#   | change comment |
#
#Scenario: match is insensitive to layout
#   Given a piece of code
#    When changing the layout of that code
#    Then the original code and changed code match

