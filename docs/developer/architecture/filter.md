# Filter

{ #dev-architecture-code-filter }

**Stable ID:** `ARCH-CODE-FILTER`

## Purpose

Document the design decisions that determine how the filter step is implemented within the find-filter-modify workflow.

## Scope

The [filter](../../user/concepts/filter.md) step refines candidate matches produced
by the [find](find.md) step by applying structural and semantic checks.
It does not modify code — that is the responsibility of the [modify](modify.md) step.

## Definition

A [filter](../../user/concepts/filter.md) function checks a set of semantic properties to ensure correctness of the transformation.

[Rice's theorem](https://en.wikipedia.org/wiki/Rice%27s_theorem) states that
all non-trivial semantic properties of programs, such as [halting](https://en.wikipedia.org/wiki/Halting_problem), are undecidable.

When a user combines multiple filter functions into a single filter function that user also becomes responsible for the diagnostics of the combination.

When a framework allows the combination of filter functions (under the `and` operator),
the framework can also provide the diagnostics for the combination.

### Decision

Filter functions have a human-readable description for diagnostic purposes.

We support undecisive filter results. In other words,
a filter function receives a match and returns one of three results:

* **include** — the match passes the check and proceeds to the modify step.
* **exclude** — the match is rejected and will not be modified.
* **undecisive** — the check cannot determine inclusion or exclusion.

The framework should provide diagnostics for each matched location. Besides the location, the diagnostics should include

* in case of rejection, the human-readable description of the filter function that rejected the location, and
* in case of indecisive, the human-readable description of the filter functions that were indecisive.

The framework enables the combination (chaining) of filter functions.
A filter function will not be executed whenever an earlier filter function returns `false`.
Note that when a filter function returns `undecisive` the next filter function will be executed.

### Switch functionality

After filtering, yet before modification a switch step could be added.
Switch functionality would enable different modifications for different situations,
for example choosing between the replacements  `f(1)` and `f($$before, 1)` depending
on whether the placeholder `$$before` is empty.

The same result can be achieved by using multiple find, filter, modify workflows with slightly different filter functions for the different situations.
In the example, one needs to duplicate the find, filter, modify workflow and extend with an additional filter
to check that the placeholder `$$before` is empty or not before applying
the replacements `f(1)` and `f($$before, 1)`, respectively.

Using multiple find, filter, and modify workflows compared to a switch step results in simpler,
yet partly duplicated logic; requires a smaller API, and hence less infrastructural development;
and a slower execution performance.

#### Decision - Switch functionality

As execution performance is not a bottleneck, switch functionality is not supported (for now).

## Invariants / guarantees

* Filter functions carry a human-readable description for diagnostic purposes.
* The framework provides diagnostics for each matched location, including:
  * in case of exclusion — the description of the filter function that rejected the location;
  * in case of undecisive — the descriptions of the filter functions that were undecisive.
* Undecisive filter results are supported.
* Filter functions are chained under `and`; execution stops early on `exclude`, not on `undecisive`.

## Related features

* [Filter concept](../../user/concepts/filter.md)

## Related tests

## Related code

## Notes
