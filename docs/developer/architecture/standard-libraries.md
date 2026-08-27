# Standard analyses and transformations

{ #dev-architecture-code-standard-libraries }

**Stable ID:** `ARCHITECTURE-CODE-STANDARD-LIBRARIES`

## Purpose

A library of standard analyses and transformations can improve quality and reuse.

## How to enable sharing given different points of view?

For this discussion, I will use the simplification from `$expr or true` to `true`.

* From a logical point of view, `$expr or true` is a tautology, so the simplification is valid.
* From a computability point of view, the simplification changes termination behavior: `$expr or true` may diverge while `true` always terminates.
  The simplification is therefore only valid when `$expr` is guaranteed to terminate.
* From an observable effects point of view, the simplification is only valid when `$expr` has no observable effect,
  such as changing the value of a variable or printing a message.
* From a specification point of view, the simplification is valid.
  An expected consequence is that trace events of all functions called from `$expr` no longer appear
  in the trace file — which is correct, since those functions are no longer called and
  the specification does not mandate their execution.

So how can we enable sharing transformations given the different points of view?

1. We could analyze and check for validity within all points of view.
   First of all, the result would be overly conservative: few transformations satisfy all views simultaneously,
   so most transformations would be rejected and never applied.
   Second, it would waste computation time and resources, as many points of view might not be considered relevant for a particular situation.
   Third, it requires upfront knowledge of all relevant points of view.

1. We could try to merge the points of view.
   For example, the tension between the observable effects and specification points of view can be resolved
   by [program slicing](https://en.wikipedia.org/wiki/Program_slicing).
   Program slicing can filter those lines of code that result in irrelevant observable effects,
   such as writing trace events, before performing the analysis for changes in observable effects.
   Like the previous proposal, it would waste computation time and resources,
   as many aspects of the merged point of view might not be considered relevant for a particular situation,
   and it requires upfront knowledge of all relevant points of view.

1. We could define transformations and analysis / filter functions independently from each other and
   make the user responsible to combine them as needed.

This approach scales as it allows points of view to be added incrementally.

### Decision

We have chosen for the last option.
For the following reasons:

1. The approach scales as it allows points of view to be added incrementally, and
1. The code owner knows best what is valid and effective for the code base.

## Filter functions

### Variables read and written

Analysis can be indecisive: external function is called with no access to the code (OS, third party library).

Possible realizations

* special set `ALL` to signal that every variable might be read or written
and special logic for union / intersection involving this special set.
* undecisive result

Note that the user would benefit tremendously when diagnostics is provided on the code location
where the indecisiveness occurs together with the symbolic call stack / chain of function calls.

## Transformation functions

### AST aware removal of node

To help the user to ensure that a removal of an AST node results in correct code,
for each language the library could provide a function to AST-aware remove a node.

Such a function should handle the corner cases, where just replacing the node's text with the empty string does not result in correct code.

This function for Python should handle at least the following examples,
when the AST node corresponding to the function call `f()` must be correctly removed.

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
These rules might be enforced by a linter, considered a good coding practice, or change the human-readable into machine-analyzable code.
Examples of such rules include

* each line contains at most one statement,
* all branches of if statements in C++ are compound statements, i.e., have brackets `{` and `}`, and
* all names are fully qualified names.

By enforcing these rules, while capturing their locations, the analyses and transformations can be kept simple.
Afterwards, the changes can be reverted at the captured locations.
