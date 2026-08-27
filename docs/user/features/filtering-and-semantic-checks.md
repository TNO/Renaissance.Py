# Filtering and semantic checks

{ #feature-filtering-and-semantic-checks }

**Stable ID:** `FEATURE-FILTERING-SEMANTIC-CHECKS`

# MISC

1. filtering

      a. Based on type, e.g., is Boolean expression?
      a. Variables written/read in code snippets (a.k.a. frame and footprint) and their intersections to determine side effects and interactions.
      a. Outside a marked area, i.e., to focus later transformations / simplifications on the areas
        where an earlier transformation took place.
        Yet see [Rewriter-Ada issue #5](https://github.com/TNO/Rewriters-Ada/issues/5) for challenges.
      a. Based on location, e.g., to exploit an analysis of another tool, such as compiler, linter,
         or type checker.
