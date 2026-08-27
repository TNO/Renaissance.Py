# architecture code base

{ #dev-architecture-code-base }

**Stable ID:** `ARCH-CODE-BASE`

## Purpose

Document the design decisions that relate to the code base that is analyzed or transformed.

## Encoding / Codec

Not only different code bases can use different text encodings, but
even within a single code base, files can have different text encodings.

Python supports a wide variety of [text encodings](https://docs.python.org/3/library/codecs.html#standard-encodings).

### Decision

We expect that the text encodings supported by Python will be sufficient for most, if not all, code bases.
Hence, we decided to depend on Python to discover the text encoding of a file,
and to read and write a file with a particular text encoding.
