# Glossary guide

{ #policy-glossary-mandatory }

**Stable ID:** `POLICY-GLOSSARY-MANDATORY`

## Status

This policy is **mandatory**.

## Scope

This policy governs the content, structure, and maintenance of [`docs/glossary.md`](../../../glossary.md) and the use of defined terms across all documentation.

---

## Purpose

The glossary is the single source of truth for short definitions of domain-specific terms.
It ensures that humans and AI tools working on this documentation use terms consistently and can trace each definition back to an authoritative concept page.

---

## When to add a term

Add a term to the glossary when **all** of the following hold:

1. The term is domain-specific — it carries meaning beyond its everyday English sense in this project's context.
2. The term appears, or is expected to appear, in more than one documentation page.
3. A concept page exists (or is planned) that serves as the authoritative source for the definition.

Do **not** add:

- General English words that need no special definition in this project.
- Implementation-specific identifiers (class names, function names) — define those inline in the relevant architecture or module page.
- Abbreviations that are standard in software engineering without a project-specific meaning (e.g., *API*, *CI*), unless the project assigns them a particular meaning.

---

## Entry format

Each glossary entry must follow this structure:

```markdown
**Term** (also: *alias*, ...)
: One or two sentence definition. Capitalize the first word; end with a period.
  Cross-references to related terms may use `[term](#anchor)` links within the glossary.
  See [Concept page title](relative/path/to/concept.md).
```

Requirements:

- The term itself is in **bold**.
- Known aliases are listed in parentheses after the term using *italics*.
- The definition uses a Markdown definition-list colon (`:`).
- The final line of every entry is a `See` link to the authoritative concept page.
- Entries are ordered **alphabetically** within lettered sections (`## A`, `## B`, …).
- Omit a lettered section if no terms begin with that letter.

---

## Relationship to concept pages

The glossary provides a **concise summary**; it does not replace the concept page.

| Glossary | Concept page |
|---|---|
| One- or two-sentence definition | Full explanation, rationale, examples, figures |
| Alphabetical index entry | Authoritative source |
| Links to the concept page | May link back to the glossary anchor |

The concept page is the authoritative source. If the definition on the concept page and the glossary entry conflict, the concept page takes precedence and the glossary entry must be updated.

---

## Maintenance rules

1. **Keep definitions in sync.** When a concept page changes a definition, update the corresponding glossary entry in the same commit or pull request.
2. **Add before first use.** A term should be in the glossary before (or at the same time as) it is first introduced in concept documentation.
3. **One entry per term.** Aliases redirect to the canonical entry using a `see` reference (e.g., `**Surround** — see [Around](#around).`).
4. **No orphan entries.** Every glossary entry must link to an existing concept page. Remove entries whose concept page has been removed.
5. **No duplicate definitions.** Do not define the same term in both a concept page and the glossary in full — the concept page holds the full definition; the glossary holds only the summary.

---

## Guidance for AI tools

When generating or editing documentation:

- Check the glossary before introducing a new term; use the existing definition and spelling if one exists.
- When creating a new concept page that introduces a domain-specific term, add a corresponding glossary entry in `docs/glossary.md`.
- When renaming a term on a concept page, update the glossary entry and all alias redirects.
- Do not add implementation-level terms (class names, method names) to the glossary.
- Preserve alphabetical ordering when inserting new entries.

---

## Enforcement

This policy is currently enforced by review. Automated checks may be added in the future.

- [CI overview](../../enforcement/ci-overview.md)
