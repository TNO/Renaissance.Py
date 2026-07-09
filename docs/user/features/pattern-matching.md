{ #feature-pattern-matching }
# Pattern matching

**Stable ID:** `FEATURE-PATTERN-MATCHING`

## User-facing summary
The system supports sequence-based, kind-based, and structural matching with placeholders and controllable matching criteria.

## Related concepts
- [Matching](../concepts/matching.md)

## Related images
- Local image directory: [pattern-matching/](pattern-matching/README.md)

# MISC

1. Match functionality
   a. Elementary matching - "symbols with symbols" - representations of  integers, characters, etc. 
   b. Basic matching - "code with code" - with(out) comment, with white spaces - note: python is sensitive for  indentation
   c. Single placeholder - "pattern with code" - pattern has only one instance of a single placeholder
   d. Multi placeholder - "pattern with code" - pattern has only one instance of a multi placeholder
   e. different placeholders - "pattern with code" with different placeholders (each placeholder occurs only once & only single assignment)
   f. constraint / recurring placeholder - "pattern with code" with single placeholder that occurs multiple times
   g. patterns with multi placeholders that can have multiple assignments
   h. mixed
