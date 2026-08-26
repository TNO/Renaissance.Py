{ #dev-architecture-test }
# Test architecture

**Stable ID:** `ARCH-TEST`

To ensure that maintainability and extensibility a test architecture is crucial.

We should use a number of testing framework.
[Browserstack describes alternatives and selection criteria](https://www.browserstack.com/guide/top-python-testing-frameworks).
* [behave](https://behave.readthedocs.io/en/latest/) for BDD tests
* pytest for unit tests
* pytest-benchmark to track our performance
* [doctest](https://docs.python.org/3/library/doctest.html) to add examples to our documentation and ensure they are correct.
  

We should at least test the following functionalities


### Find Functionality
* Find kind (nested)
  * Example, find if statements 
  * A found match can contain another found match
  * Support language agnostics kinds
    * Definition, statement, expression, ...
  * Support parser specific kinds
    * e.g. IASTIfStatement 
  * To be decided: support of kind patterns (like XPath)?
* Find AST Pattern (nested)
  * Example, find `if ($x == MAX) { $$stmts; }`
  * A found match can contain another found match 
* Find AST Pattern consecutive, i.e., the found matches do not overlap
  * Find "aa" in "aaa" has only one match
  * Find "aa" in "aaaa" has only two non-overlapping matches 

### Navigation Functionality
* AST structure
  * Parent & Ancestors
  * Children & Descendants
  * Siblings
* Usage
  * definition / (forward) declaration - references (ONLY in current file / analysis unit)  
* Inheritance
  * Base - Derived classes 

### Transformation Functionality

* The encoding of a file should never be changed
* The meta data of a file or directory is only allowed to change when an actual change happened
  * Analysis or a match (with a failing filter) are NOT enough
* Offset-based batch modifications of strings
  * Insert and replace operations
    * remove is just replace with ""
  * Containment rule: contained operations are ignored
  * Consistency rule: overlapping operations are not possible
  * To be decided: 
    * Are overlapping, contained operations just ignore, a warning, or an error?
    * Are overlapping removals allowed?
* AST-based batch modifications of strings
  * Prepend, append, replace, around (e.g., for matching brackets) 
  * Containment rules: 
    * A replace operation on an AST node, hides all operations on all contained AST nodes (a.k.a. descendants), i.e., they are ignored - prepend, append and around operations on that AST node are NOT affected.
    * A prepend to an AST node is always before a prepend to any contained AST node
    * An append to an AST node is always after an append to any contained AST node
  * Sequence rule - Given two consecutive AST Nodes (a.k.a. siblings): 
    * An append to the first AST Node is always before a prepend to the second AST Node
* Batch modification of Translation Unit (Single file of code)
  * Prepend, append, around, replace of specific AST Node
  * Find, Filter (possibly multiple), and Replace functionality (whole match is replaced)
    * Replace recursively (so the AST nodes assigned to placeholders are also modified)
  * Find (possibly multiple), Filter (possibly multiple), and modify functionality 
    * Multiple operations on a single find
    * Modification of any AST node possible
      * not only contained in the find, but all via navigation (along parent and ancestor nodes)


# placeholder requirements

To ensure that maintainability and extensibility a test architecture is crucial.

We should use a number of testing framework.
[Browserstack describes alternatives and selection criteria](https://www.browserstack.com/guide/top-python-testing-frameworks).
* [behave](https://behave.readthedocs.io/en/latest/) for BDD tests
* pytest for unit tests
* pytest-benchmark to track our performance
* [doctest](https://docs.python.org/3/library/doctest.html) to add examples to our documentation and ensure they are correct.
  

We should at least test the following functionalities

### Code Matching Functionality
* Independent of layout (whitespaces) and comments (presence, absence, content)
* Support of placeholders
  * Placeholders are AST Nodes
  * Support of explicit and implicit placeholders
  * Robustness for occurrence of implicit placeholders
    * in strings, e.g. `"$X"`
    * in comments, e.g., `/* $X */`.
  * Multiple occurrences of placeholders
    * Equivalent AST nodes
    * Access to all occurrences
  * Multiple assignments of placeholders
    * E.g., in patterns like `$f($$before, $arg, $$after)`

### Find Functionality
* Find kind (nested)
  * Example, find if statements 
  * A found match can contain another found match
  * Support language agnostics kinds
    * Definition, statement, expression, ...
  * Support parser specific kinds
    * e.g. IASTIfStatement 
  * To be decided: support of kind patterns (like XPath)?
* Find AST Pattern (nested)
  * Example, find `if ($x == MAX) { $$stmts; }`
  * A found match can contain another found match 
* Find AST Pattern consecutive, i.e., the found matches do not overlap
  * Find "aa" in "aaa" has only one match
  * Find "aa" in "aaaa" has only two non-overlapping matches 



# placeholder requirements

A.	We want placeholders at higher level than name to match more complicated AST nodes.
Some examples

| match pattern |  with code |
| --------------- | ------------ | 
|   int $$x;          |    int a=4, b=5, c; | 
|   $type v;         |    const myclass v; | 
|   x = $expr;    |    x = 1 + 2; | 
|   $x;                 |    a = f(1,2+3); | 
 
Note that although the placeholder node is an IASTName the matching instance node doesn't need to be!
 
The function getPlaceholderName specifies what we consider a placeholder:
ASTNode that contains nothing else than a name at the lowest level!
 
Since in some cases multiple levels are above an IASTName the function getPlaceholderName is implemented recursively.
 
Note that in the match of `$x;` the concrete syntax of the placeholder name `$x` is different than the concrete syntax of the statement `$x;`!
 
A placeholder can match multiple ASTNodes: e.g. IASTName and IASTIdExpression
We prefer the highest ASTnode


B.	We want to support that placeholders can occur multiple times
This expresses a constraint: same placeholder enforces same value in instance
 
Unfortunately, the same placeholder can have multiple classes in a single pattern!
We are aware of the following cases in C++  (in arbitrary order)

1. 	$type* ptr = new $type();
        Class of $type is first IASTNamedTypeSpecifier and second IASTTypeId
2.	const $type* ptr = new $type();
        Class of $type is first IASTName and second IASTTypeId
3.	{ int $x = 1; int y = $x; }
        Class of $x is first IASTName and second IASTIdExpression
4.	int $var; $var = 1;
       Class of $var is first IASTDeclarator and second IASTIdExpression
5.	$f; var = $f;
       Class of $f is first IASTExpressionStatement and second IASTIdExpression
6.	var = $f; $f;
       Class of $f is first IASTIdExpression and second IASTExpressionStatement
 
Hence, we can't just compare instances related to the same placeholder (because they will be of different classes)
 
How can it be done?
The fifth and sixth cases show

1.	It is not limited to declarations and references (so using the declarations and references in the pattern and check that the instances have similar relations will only solve part of the problem).
2.	The comparison of the ASTNodes is not a comparison of IASTNames:
     We have to compare expressions (the arguments) of the instance f(1); x = f(2); 
     to find that it doesn't match the pattern $f; $var = $f;
 
Solution:
Pick the highest AST node allowed by the all placeholder together in the pattern!

# equivalent code

### When is code equivalent?

* Syntax
* Semantics
  * Representations
    * Are there tokenizers / lexers that already hide the different representations?
    * How are string constants matched in Python? Does the lexer make the same token for "ape" and 'ape'?

| Representation | Example | Base case |
| ---------------- | ---------- | ---------- | 
| Readability (e.g. Underscores   in Numeric Literals) | 1_000_000  | 1000000 |
| scientific | 1E2 | matches | 100 |
| base (2,8,10,16,…) | 0xFF | matches | 255 | 
| String | "ape" | 'ape' | 
| String   concatenation | "con"   "cat" | "concat" | 

  * Symmetry
    * Operators, like ==, are symmetric (for some data types), and hence `0 == x` matches 	`x == 0`
			
  * Purpose
    * E.g. in C++ exist multiple ways to initialize a variable:	`int x = 1;` matches `int x { 1 };` and `int x(1);`

# BDD framework

Which BDD framework should we pick?
I got from Paul the following input.

<html>
<body>
<!--StartFragment--><span data-teams="true"><h1><span style="font-size: x-large;">Python BDD Framework Recommendation Based on Maturity, Support, and Usage</span></h1><p><span style="font-size: inherit;">When evaluating Python BDD frameworks based on maturity, support, and community adoption, here's a more detailed analysis:</span></p><h2>Comparative Analysis</h2>

| Framework | Maturity | Community Support | Usage/Popularity | GitHub Stats (approx.) |
| -- | -- | -- | -- | -- |
| pytest-bdd | High (stable since 2013) | Strong pytest ecosystem | High and growing | 1.2k+ stars, regular updates |
| Behave | Very High (stable since 2011) | Dedicated community | Very High | 2.5k+ stars, active maintenance |
| Robot Framework | Very High (since 2008) | Large enterprise adoption | Very High | 7k+ stars, corporate backing |
| Lettuce | Medium | Limited (less active) | Declining | 1.2k+ stars, minimal updates |

<h2>Recommendation: pytest-bdd</h2><p><span style="font-size: inherit;"><strong>For most modern Python codebases, I recommend pytest-bdd</strong> for these reasons:</span></p><ol><li><strong>Ecosystem Integration</strong>: It integrates seamlessly with pytest, which is the de facto standard for Python testing. If you're already using pytest (which most Python projects do), this means:
<ul><li>Shared fixtures</li><li>Same command-line interface</li><li>Compatible plugins</li><li>Familiar reporting</li></ul></li><li><strong>Active Development</strong>: Regular updates and maintenance with good GitHub activity</li><li><strong>Modern Python Support</strong>: Excellent support for recent Python versions</li><li><strong>Strong Documentation</strong>: Clear, comprehensive documentation with examples</li><li><strong>Industry Adoption</strong>: Used by many companies including some large enterprises</li></ol><h2>Strong Alternative: Behave</h2><p><span style="font-size: inherit;">Behave is a very close second and might be preferable if:</span></p><ul><li>You want something that feels more like traditional Cucumber</li><li>You need a standalone BDD solution not tied to pytest</li><li>You prefer its slightly more mature feature set</li></ul><p><span style="font-size: inherit;">Behave has slightly higher raw usage numbers historically, but pytest-bdd is gaining ground rapidly due to pytest's dominance in the Python ecosystem.</span></p><h2>Robot Framework Consideration</h2><p><span style="font-size: inherit;">Robot Framework deserves mention as the most comprehensive option with the largest enterprise adoption, but it's:</span></p><ul><li>Much more than just a BDD tool (full test automation framework)</li><li>Has a steeper learning curve</li><li>May be overkill if you just need BDD capabilities</li></ul></span><!--EndFragment-->
</body>
</html>