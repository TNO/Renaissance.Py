{ #concept-filter }
# Filter

**Stable ID:** `CONCEPT-FILTER`

## Purpose
Filtering refines candidate matches by applying semantic or structural checks.

## Practical consequence
A filter result may be include, remove, or undecisive.


# MISC

1. When occurrence of a placeholder changes, either by number or conditions, the behaviour is changed whenever that "placeholder has a side effect" / the set of variables written by the placeholder is not empty.
2. When the (execution) order of placeholders changes, the behaviour is changed whenever those "placeholders have an effect on each other" / at least one of the intersections between the variables written and read by the different placeholders is not empty.
