# Assigned To Human

## Blurb

A host is issued to this person as theirs to use.

## Purpose

Joins a machine to the person an asset inventory or MDM records as its user, on identity_core's human, where that person's accounts in every other system also resolve. Requirements: `req-computing-core-host-edges`.

## Goals

- "Which machines does this person use?" and "who uses this machine?" as one hop.
- A host with no assignment, and a person's account with no machine, as visible states.

## Identity

Edges carry no natural key; ids are assigned (`req-grid-entity-natural-key`). More than one edge from one host is a shared or pooled machine and is kept.

## Boundaries

- Not responsibility for a server (who operates a machine is a different relationship, not built).
- Not an OS account on the machine.
- Never inferred from a hostname or display name; drawn by whoever knows the assignment.

## Neutrality

Vendor-neutral: both endpoints are substrate types.

## Observability

**Not observed.** Drawn by an operator seed or an inventory feed; no collector emits it yet.

## Authoritative Source

- **Source:** computing-core#8 and George's ruling Q61 (2026-09-24)
- **Version:** tap-plugin-computing-core main, 2026-09-24
- **Retrieved:** 2026-09-24

## Prior Art

- `HELD_BY_HUMAN__identity_core` (identity_core v0.1.3): the account-side equivalent, onto the same target.

## Endpoints

- Source `computing_core__host`; target `identity_core__human`.
- Stamps `tap.computing` = `identity`.
