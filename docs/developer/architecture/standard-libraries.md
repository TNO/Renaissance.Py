{ #dev-architecture-code-standard-libraries }
# Standard analyses and transformations

**Stable ID:** `ARCHITRECTURE-CODE-STANDARD-LIBRARIES`

## Purpose
A library of standard analyses and transformations can improve quality and reuse.

## Filter functions

### Variables read and written

Analysis can be indecisive: external function is called with no access to the code (OS, third party library).

Possible realizations
* special set `ALL` to signal that every variable might be read or written 
and special logic for union / intersection involving this special set.
* undecisive result

Note that the user would benefit tremendously when diagnostics is provided on the code location where the indecisiveness occurs together with the symbolic call stack / chain of function calls.

## Transformation functions

### AST aware removal of node

To help the user to ensure that a removal of an AST node results in correct code, for each language the library could provide a function to AST-aware remove a node.

Such a function should handle the corner cases, where just replacing the node's text with the empty string does not result in correct code.

This function for Python should handle at least the following examples, when the AST node corresponding to the function call `f()` must be correctly removed. 

#### Example separator
Original code
```python
f() ; g()
```
correct removal includes separator `;` 
```python
g()
```

#### Example empty else branch
Original code
```python
if cond:
    g()
else:
    f()
```
correct removal includes removal of `else` keyword 
```python
if cond:
    g()
```

#### Example empty then branch
Original code
```python
if cond:
    f()
else:
    g()
```
correct removal includes negation of the condition 
```python
if not cond:
    g()
```

#### Example side-effect in condition
Original code
```python
if x := cond:
    f()
```
correct removal requires that side effect is kept,
so either 
```python
if x := cond:
    pass
```
or
```python
x = cond
```

## prepare / restore function

Analyses and transformations can benefit when the code adheres to some `rules`.
Examples of such rules include 
* each line contains at most one statement
* all branches of if statements in C++ are compound statements, i.e., have brackets `{` and `}`.

These rules might be enforced by a linter or considered a good practice.

By capturing and removing all violations of such rules, the analyses and transformations can be kept simple.
Afterwards, the violations can be reinserted at the captured locations.
