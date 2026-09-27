# Represents Host

## Blurb

A vendor's record of a device is a record of this host.

## Purpose

Lets every vendor's device record (Okta device, Duo endpoint, Teleport trusted device, MDM, EDR) converge on one neutral host without computing_core naming any vendor. Requirements: `req-computing-core-host-edges`.

## Goals

- One node per machine however many vendors see it.
- A vendor record that points at no host is the unmatched state a device review shows.

## Identity

Edges carry no natural key; ids are assigned (`req-grid-entity-natural-key`). A record pointing at two hosts is a mismatch, kept so it can be seen.

## Boundaries

- The source is wildcard: nothing here can tell a device record from any other type, so whoever draws the edge keeps that promise, and a traversal that wants device records only filters the source type.
- Never inferred from a shared hostname.

## Neutrality

Vendor-neutral target, open source side: the pattern of `HELD_BY_HUMAN__identity_core`.

## Observability

**Not observed.** Drawn by an operator seed or a collector's match; no collector emits it yet.

## Authoritative Source

- **Source:** George's ruling Q61 (2026-09-24) and computing-core#8
- **Version:** tap-plugin-computing-core main, 2026-09-24
- **Retrieved:** 2026-09-24

## Prior Art

- `HELD_BY_HUMAN__identity_core` (identity_core v0.1.3): the same wildcard-source convergence for accounts.
- BloodHound OpenGraph Okta extension `Okta_DeviceOf` (read 2026-09-22 by the okta corpus): a vendor device tied to its user, not to a neutral machine.

## Endpoints

- Source: any type (wildcard); target `computing_core__host`.
- Property `matched_on`: how the record was tied to the host (serial number, asset tag, operator seed); blank is not recorded.
- Stamps `tap.computing` = `host`.
