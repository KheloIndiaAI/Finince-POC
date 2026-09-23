# Sanction vs UC Comparison — Engineering Guide

READ THIS FIRST, before writing or changing any code. If a change conflicts
with what's linked below, stop and ask rather than guessing.

The engineering docs are split into four files under `engineering_doc/`.
Read all four before your first change to this repo, then keep them open
as reference:

- `engineering_doc/coding-standards.md` — the non-negotiable principles,
  prompt rules, testing rules, and definition of done.
- `engineering_doc/architecture.md` — what the system does, MVP-1 scope,
  the extracted fields, the flow diagram, the data model, and the tech stack.
- `engineering_doc/schema.md` — every table's columns, types, keys, and the
  entity-relationship diagram. `app/models.py` is the source of truth;
  update this file when the models change.
- `engineering_doc/local-setup.md` — how to run it locally (Docker Compose),
  run the tests, and how it deploys (AWS EC2).

The build roadmap and current step status live in README.md.
