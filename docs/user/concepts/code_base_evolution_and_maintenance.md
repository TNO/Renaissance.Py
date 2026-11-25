<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Evolving and maintaining code

{ #concept-code-base-evolution-and-maintenance }

**Stable ID:** `CONCEPT-CODE-BASE-EVOLUTION`

## Purpose

This concept describes the software landscape that the repository targets: evolving and maintaining a code base over time.

## Definition

A **code base** is changed to

* fix bugs and security vulnerabilities,
* add new features,
* respond to external changes and obselescence of components, interfaces, and tooling, and
* improve quality aspects, such as performance and maintainability.

A code base

* comprises production, validation, and supporting artifacts, including source code, tests, build scripts, and documentation,
* is organized in multiple hierarchical folders and/or projects,
* is typically written using multiple programming languages,
* depends on external libraries, APIs, OSes, and services,
* may evolve over decades, with developers and maintainers joining and leaving,
  creating a need for adequate knowledge management to preserve knowledge.
