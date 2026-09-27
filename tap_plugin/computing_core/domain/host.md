# Host

## Blurb

An environment that runs an operating system and executes programs: a laptop, a phone, a server, a virtual machine, a container or a CI runner.

## Purpose

The neutral machine an identity acts from and a job runs on. Vendors each keep their own record of a device (an Okta device, a Duo endpoint, a Teleport trusted device, an MDM or EDR record); those records point here with `REPRESENTS_HOST`, so four vendors' views of one laptop converge on one node, and the laptop reaches the person it is issued to with `ASSIGNED_TO_HUMAN`. Requirements: `req-computing-core-host` in `specs/spec-computing-core-v0.md`.

## Goals

- Answer "which machines does this person use, and are they managed?" across every vendor that sees the machine.
- Give the authoring endpoint and the runner host (github-core#127, stations B1 and E1) a node to land on before any sensor observes them.
- Show a vendor device record that matches no host, and a host no vendor knows, as the unmatched states a device review looks for.

## Identity

Natural key: `asset_tag`. It is assigned, so every form factor has one, and it survives a rename, an OS reinstall and a disk swap. A hardware serial is not the key: a container has none, a virtual machine's is blank, cloned or a placeholder, and serials are unique only per manufacturer. A serial is how a collector often matches a vendor record to a host, and that match is recorded on `REPRESENTS_HOST` (`matched_on`).

## Boundaries

- Not hardware. No CPU, chassis, disk, NIC or serial: `req-computing-core-scope-1` keeps physical hardware out, and `form_factor` classifies the operating environment, not the machine.
- Not an OS account. A login on the machine ("a Linux user") is a different concept, not built.
- Not a web host. `web_host` is an internet name serving HTTP.
- No free-form `configuration` field (`req-computing-core-models-7`).
- How a host is used (a runner, an ephemeral environment) is not a `form_factor` value; it becomes its own field when a consumer needs it.

## Neutrality

Vendor-neutral. The test: every vendor device record and every CI provider's runner describes an instance of this concept, and none of the fields is specific to one of them.

## Observability

**Not observed.** No collector mints hosts yet; a host is seeded by an operator or drawn by a consumer plugin. Vendor device records carry the facts that would fill it (Okta: platform, OS version, managed; Teleport: asset tag, OS type; Duo: OS, device name), and none has been executed against for this plugin.

## Authoritative Source

- **Source:** Open Cybersecurity Schema Framework (OCSF), `objects/endpoint.json` `type_id` (device type) and `objects/device.json` (`is_managed`, `is_personal`)
- **Version:** OCSF 1.6.0 (github.com/ocsf/ocsf-schema tag v1.6.0)
- **Retrieved:** 2026-09-24

## Prior Art

- OCSF 1.6.0 device object (retrieved 2026-09-24): `type_id` Unknown, Server, Desktop, Laptop, Tablet, Mobile, Virtual, IOT, Browser, Firewall, Switch, Hub, Router, IDS, IPS, Load Balancer, Other; `is_managed`, `is_personal`.
- computing-core#8 (2026-09-14): the `host` proposal with a `kind` field, refined here to `form_factor`.

## Fields

- `asset_tag` — The operator's stable identifier for the machine: an inventory asset tag for a device, the assigning system's stable name for a runner or container. Required; the natural key.
- `name` — Display name (a hostname, a runner name). Not identity: it changes on rename.
- `form_factor` — OCSF's device types that bear an operating system (`desktop`, `laptop`, `tablet`, `mobile`, `server`, `virtual`, `iot`, `unknown`) plus `container`. Blank is not observed; `unknown` is observed and unclassifiable.
- `os` — The operating system as reported, free text, until an `operating_system` node exists.
- `managed` — Enrolled in device management (MDM), OCSF `is_managed`. Null is not observed; false is observed unenrolled.
- `ownership` — `corporate` or `personal` (bring-your-own), OCSF `is_personal`. Blank is not observed.
