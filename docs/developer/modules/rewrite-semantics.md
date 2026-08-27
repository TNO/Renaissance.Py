# Rewrite semantics test module

{ #testmod-rewrite-semantics }

**Stable ID:** `TESTMOD-REWRITE-SEMANTICS`

## Corner cases for test the rewrite seamatics

1. AST node spanning the whole file, i.e., the complete range.
2. AST beginning at the start of the file, i.e., the range starts at the first character.
3. AST stopping at the end of the file, i.e., the range ends at the last character.
   Last character might be End-Of-File (`EOF`) instead End-Of-Line (`EOL`).
