{ #feature-filtering-and-semantic-checks }
# Filtering and semantic checks

**Stable ID:** `FEATURE-FILTERING-SEMANTIC-CHECKS`

# MISC 

4. filtering
      a. Based on type, e.g., is Boolean expression?
      b. Variables written/read in code snippets (a.k.a. frame and footprint) and their intersections to determine side effects and interactions.
      c. Outside a marked area, i.e., to focus later transformations / simplifications on the areas where an earlier transformation took place 
        [Yet see https://github.com/TNO/Rewriters-Ada/issues/5 for challenges]
      d. based on location, e.g., to exploit an analysis of another tool (compiler, linter, type checker, ...)