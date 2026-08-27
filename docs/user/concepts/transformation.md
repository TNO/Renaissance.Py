{ #concept-transformation }
# Transformation

**Stable ID:** `CONCEPT-TRANSFORMATION`

## Purpose
Transformation manipulates code using find / filter / manipulate workflows.

# MISC

### Transformation Functionality

* The encoding of a file should never be changed
* The meta data of a file or directory is only allowed to change when an actual change happened
  * Analysis or a match (with a failing filter) are NOT enough
* Offset-based batch modifications of strings
  * Insert and replace operations
    * remove is just replace with ""

* AST-based batch modifications of strings
  * Replace (incl. remove), and insert (Prepend, append, and surround - e.g., for matching brackets)

* Batch modification of Translation Unit (Single file of code)
  * Prepend, append, surround, replace of specific AST Node
  * Find, Filter (possibly multiple), and Replace functionality (whole match is replaced)
    * Replace recursively (so the AST nodes assigned to placeholders are also modified)
  * Find (possibly multiple - a.k.a. chained find), Filter (possibly multiple), and modify functionality
    * Multiple operations on a single find
    * Modification of any AST node possible
      * not only contained in the found match, but all via navigation (along parent and ancestor nodes)

