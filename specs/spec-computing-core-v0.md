# Computing Core Plugin Specification

## Philosophy

The Computing Core plugin provides the vendor-neutral primitives needed to describe modern computing systems above hardware and below higher-level cloud-provider and application-domain abstractions. It is the layer where TAP begins to talk about virtual machines, containers, operating systems, filesystems, interfaces, IP addressing, ports, processes, programs, and network connections in a way that applies across cloud and on-prem environments.

The demarcation line for v0 is intentional. This plugin starts above physical hardware and below provider-specific infrastructure modeling. It should not try to describe chassis, disks, routers, switches, or specialized cloud constructs in provider-native terms. It should also avoid prematurely collapsing into product- or business-level concepts such as "service" and "application" where the project has not yet agreed on stable semantics.

The plugin favors durable primitives over convenience abstractions. If a concept is likely to remain meaningful across Linux hosts, containers, virtual machines, AWS, and on-prem environments, it belongs here. If it is provider-specific, orchestration-specific, or still semantically fuzzy, it should be deferred or modeled in a more specific plugin.

Networking is an especially important part of this layer. v0 should model the stable pieces of IP-based networking that are useful for graph traversal and system understanding without overcommitting to packet-level or datagram-level modeling. That means durable endpoint and session concepts now, with richer flow and protocol work later.

## Goals

|    |              |                                                                 |
| :---: | ---       | ---                                                             |
| 1. | Vendor-Neutral | Models capture generic computing and IP-networking primitives rather than provider-specific resources |
| 2. | Durable      | v0 prioritizes concepts likely to survive across environments and future plugins |
| 3. | Expressive   | Relationships favor semantically meaningful edge types over generic catch-all links |
| 4. | Dimensioned  | Every TAP-managed type in the plugin uses meaningful `tap.computing` default dimensions |
| 5. | Evolvable    | The plugin leaves clear room for deeper protocol, flow, and provider-integration work later |

## Requirements

| RID | Name | Status | Notes |
| --- | --- | :---: | --- |
| req-computing-core-scope | [Plugin Scope](#plugin-scope) | Proposed | Defines what Computing Core covers and excludes |
| req-computing-core-dimensions | [Dimension Strategy](#dimension-strategy) | Proposed | `tap.computing` dimensions and dimension-node experiment |
| req-computing-core-models | [Model Catalog](#model-catalog) | Proposed | Vendor-neutral model set for compute, storage, runtime, and networking |
| req-computing-core-host | [Host](#host) | Implemented | `computing_core__host`: the OS-bearing environment an identity acts from and a job runs on; `form_factor` from OCSF's device types; keyed on `asset_tag` |
| req-computing-core-host-edges | [Host Edges](#host-edges) | Implemented | `ASSIGNED_TO_HUMAN` (host → `identity_core__human`) and `REPRESENTS_HOST` (any vendor device record → host) |
| req-computing-core-ip | [IP Version Support](#ip-version-support) | Proposed | IPv4 and IPv6 are first-class supported capabilities |
| req-computing-core-ports | [Port Modeling](#port-modeling) | Proposed | Ports are first-class nodes with simple v0 state semantics |
| req-computing-core-interface | [Network Interface Modeling](#network-interface-modeling) | Proposed | `network_interface` MAC uses `null` for unobserved/not-applicable (partial-observation convention) |
| req-computing-core-tcp | [TCP Connection Modeling](#tcp-connection-modeling) | Proposed | TCP connections are modeled as nodes rather than edges |
| req-computing-core-protocols | [Protocol Scope](#protocol-scope) | Proposed | v0 stops just above layer four with generic application protocol modeling |
| req-computing-core-edges | [Edge Types](#edge-types) | Proposed | Expressive edge family for structural and runtime relationships |
| req-computing-core-reference | [Reference Data](#reference-data) | Proposed | Dimension nodes and any seed taxonomy data |
| req-computing-core-validation | [Plugin Validation](#plugin-validation) | Proposed | Structural validation now; deeper levels encouraged before publication |
| req-computing-core-nongoals | [v0 Non-Goals](#v0-non-goals) | Proposed | Explicitly deferred concerns |

### Plugin Scope
----
RID: `req-computing-core-scope`

Status: `Proposed`

The Computing Core plugin models modern computing infrastructure primitives above hardware and below provider-specific cloud resources and higher-level product/application abstractions.

#### Implementation

The plugin covers:

- compute runtime units such as virtual machines and containers
- host/runtime environment such as operating systems
- storage primitives such as filesystems and files
- runtime execution primitives such as programs and processes
- network attachment primitives such as interfaces, IP addresses, subnets, and ports
- transport/session primitives such as TCP connections
- generic application-protocol concepts above transport but below concrete protocols like HTTP or DNS

The plugin excludes in v0:

- physical hardware
- provider-native infrastructure resources such as VPCs, EBS volumes, Elastic IPs, and AWS subnets
- deep network packet or hop modeling
- concrete application protocols such as HTTP, TLS, DNS, SSH, and SMTP
- unstable higher-level concepts such as "service" and "application" until those semantics are better defined

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-scope-1 | Above Hardware | Proposed | The plugin starts at the virtual-machine/container layer rather than modeling physical hardware. | Read 2026-09-24 (computing-core#8): `host` is in scope because it is the OS-bearing environment, not the hardware. A laptop's `host` node is the operating environment someone uses; it carries no CPU, chassis, disk, NIC or hardware serial, and a `form_factor` of `laptop` classifies the environment rather than modelling the machine. |
| req-computing-core-scope-2 | Vendor Neutral | Proposed | v0 models generic primitives rather than provider-native resources. | |
| req-computing-core-scope-3 | Stable Semantic Focus | Proposed | Ambiguous higher-level concepts are deferred until TAP defines them more clearly. | |

#### Future

Later work may split networking and protocol concerns into dedicated plugins or use additional dimensions to distinguish networking subdomains while preserving Computing Core as the foundational generic layer.

### Host
----
RID: `req-computing-core-host`

Status: `Implemented`

`computing_core__host` is an environment that runs an operating system and executes programs: a laptop, a phone, a desktop, a server, a virtual machine, a container, a CI runner. It is the neutral machine an identity acts from and a job runs on (computing-core#8; github-core#127). Vendor records of a device (an Okta device, a Duo endpoint, a Teleport trusted device, an MDM or EDR record) are separate nodes in their own plugins that point here with `REPRESENTS_HOST`.

#### Implementation

`tap_plugin/computing_core/models/host.py` defines `Host(BaseModel)`, `ENTITY_TYPE = "computing_core__host"`, `ENTITY_ICON = "host"`, `DEFAULT_DIMENSIONS = {"tap.computing": "host"}`. Article: `tap_plugin/computing_core/domain/host.md`. Migration `0005_host` (depends on `tap_grid` `0001_initial`, the floor).

| Field | Meaning |
| --- | --- |
| `asset_tag` | Required. The operator's stable identifier for the machine: an inventory asset tag for a device, the assigning system's stable name for a runner or container. The natural key. |
| `name` | Display name (a hostname, a runner name). Not identity. |
| `form_factor` | One of `desktop`, `laptop`, `tablet`, `mobile`, `server`, `virtual`, `container`, `iot`, `unknown`, or blank. |
| `os` | The operating system as reported, free text. |
| `managed` | Enrolled in device management (MDM). `null` = not observed, `false` = observed unenrolled. |
| `ownership` | `corporate`, `personal`, or blank = not observed. |

**One field, `form_factor`, not the issue's `kind`.** computing-core#8 proposed a `kind` of `workstation · server · virtual_machine · container · ephemeral_runner · cloud_dev_environment · unknown`. That list mixes three questions: what shape the machine is (workstation, server), whether it is virtualised (virtual machine, container), and how it is used (a runner, a cloud dev environment, ephemeral). A value can answer only one, so a GitHub-hosted runner is both `virtual_machine` and `ephemeral_runner` and the collector must pick. `form_factor` answers only the first two, which are one axis in practice, and uses OCSF's device `type_id` captions (OCSF 1.6.0, `objects/endpoint.json`) because the security tools whose records point here (EDR, MDM, identity providers) already classify devices that way, so mapping a vendor record is a lookup rather than a judgement. From OCSF: `server`, `desktop`, `laptop`, `tablet`, `mobile`, `virtual`, `iot`, `unknown`. Left out: `browser` (not an operating system), and `firewall`, `switch`, `hub`, `router`, `ids`, `ips`, `load balancer` (network appliances, below this plugin's floor and in the excluded hardware set). Added: `container`, which OCSF models as a separate object rather than a device type. `unknown` means a source was asked and could not classify (OCSF's `0`); blank means nobody has said. How a host is used (runner, ephemeral) is a separate fact and becomes its own field when a consumer needs it, not a `form_factor` value.

**Identity: `asset_tag`, not a hardware serial.** The key must exist for every form factor, survive a rename, an OS reinstall and a disk swap, and be unique within one grid. An asset tag is assigned, so it meets all three. A hardware serial fails the first: a container has none, a virtual machine reports a blank, cloned or placeholder value ("To Be Filled By O.E.M.", "0"), and serials are unique only per manufacturer. It is also a hardware fact, which scope-1 keeps off this type. A serial number is still how a collector often *matches* a vendor record to a host; that is recorded on the `REPRESENTS_HOST` edge (`matched_on`), not used as the host's identity. Never a name alone: `name` changes on rename and is not part of the key.

No free-form `configuration` field (req-computing-core-models-7): no named source fills one.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-host-1 | Host Type | Implemented | `computing_core__host` exists with the fields above, `tap.computing: host`, the `host` icon, a domain article and migration `0005_host`. | `tests/test_host.py::TestHostModel` |
| req-computing-core-host-2 | Keyed On Asset Tag | Implemented | `NATURAL_KEY = ("asset_tag",)`; `asset_tag` is required on create; the key survives a rename. | `tests/test_host.py::TestHostModel::test_identity_is_the_asset_tag` |
| req-computing-core-host-3 | Three States | Implemented | Blank `form_factor`/`ownership`/`os` and `null` `managed` mean not observed; `managed = false` is an observation. | `tests/test_host.py::TestHostModel::test_unobserved_fields_stay_unobserved` |
| req-computing-core-host-4 | Closed Vocabularies | Implemented | `form_factor` and `ownership` refuse values outside their lists. | `tests/test_host.py::TestHostModel::test_closed_vocabularies_refuse_other_values` |

#### Future

- An `ephemeral` / usage field (runner, cloud dev environment) when a consumer needs it (computing-core#8's `ephemeral`).
- A machine-local account (an OS login on a host, "a Linux user"): a separate concept, not built.
- computing-core#8's remaining items are not built here: the `identity` id-minting module, `HOLDS_PRIVATE_KEY` and `KEY_PAIR`.

### Host Edges
----
RID: `req-computing-core-host-edges`

Status: `Implemented`

Two edges tie the neutral host to the person it is issued to and to the vendor records that describe it.

#### Implementation

| Edge | Source → target | Properties | Dimensions |
| --- | --- | --- | --- |
| `ASSIGNED_TO_HUMAN__computing_core` | `computing_core__host` → `identity_core__human` | none (closed, empty schema) | `tap.computing: identity` |
| `REPRESENTS_HOST__computing_core` | any type (wildcard) → `computing_core__host` | `matched_on` (string) | `tap.computing: host` |

**`ASSIGNED_TO_HUMAN`** records that a host is issued to a person as theirs to use: the primary user an asset inventory or MDM records. It is not responsibility for a server and not an OS account. The `_TO` is the relational preposition of an assignment predicate, like `BELONGS_TO_ACCOUNT`, not a direction marker; the slug ends in its object noun. The target is identity_core's human, so a person's laptop and their Okta, Duo and Teleport accounts meet on one node. Owned here rather than as another wildcard edge in identity_core because both endpoints are known: computing_core owns the source type, and naming identity_core's type is a declared vocabulary dependency (`depends_on` identity_core `>= 0.1.3`, the first release with `identity_core__human`). identity_core depends on nothing, so no cycle forms, and the dependency points from one substrate to another, never up to a vendor plugin. computing-core#8's `OWNS_HOST` (user → host) is not built: its source was `user`, which Q60 retires, and "owns" named responsibility, which is not what an inventory records.

**`REPRESENTS_HOST`** records that a vendor's device record describes this host. The source is wildcard, the same pattern as `HELD_BY_HUMAN__identity_core`: any vendor's device type points here without computing_core depending upward on the vendor. A vendor plugin declares it in its device model's `OUTBOUND_EDGES` and depends on computing_core. `matched_on` says how the record was tied to the host (a serial number, an asset tag, an operator seed); blank means not recorded.

Neither edge is containment: a host does not retire with a person or a vendor record, nor they with it.

Endpoint lists are enforced under the grid's permission union (`req-grid-edge-constraints-3`): a node type that declares no `OUTBOUND_EDGES`/`INBOUND_EDGES` is unconstrained on that side.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-host-edges-1 | Assigned To Human | Implemented | A host may be assigned to one or more humans; the edge carries no properties; identity_core `>= 0.1.3` is the declared dependency and the only foreign type named. | `tests/test_host.py::TestAssignedToHuman`, `::test_identity_core_is_the_declared_vocabulary_dependency` |
| req-computing-core-host-edges-2 | Represents Host | Implemented | Any node may point at a host; `matched_on` is the only property. | `tests/test_host.py::TestRepresentsHost` |
| req-computing-core-host-edges-3 | Endpoints Declared | Implemented | The edge files declare the endpoints above and closed property schemas. | `tests/test_host.py::test_edge_endpoints_are_declared` |

### IP Version Support
----
RID: `req-computing-core-ip`

Status: `Proposed`

IPv6 is a first-class supported capability alongside IPv4.

#### Implementation

The plugin should be designed so IPv4 and IPv6 work naturally anywhere generic IP concepts appear. At minimum, this includes:

- `ip_address`
- `ip_subnet`
- `network_interface` relationships to addresses
- any port and connection modeling that depends on address identity

IPv6 support should not be treated as an afterthought or left to provider-specific plugins. If a generic computing/networking concept can apply to IP addressing, the v0 design should assume both IPv4 and IPv6 are in scope unless there is a concrete reason to defer a detail explicitly.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-ip-1 | IPv4 And IPv6 Supported | Proposed | Generic IP primitives support both IPv4 and IPv6. | |
| req-computing-core-ip-2 | Interface Relationships Support IPv6 | Proposed | Interface-to-address relationships accommodate IPv6 without special-case redesign. | |
| req-computing-core-ip-3 | No IPv4-Only Assumptions | Proposed | v0 model design avoids accidental IPv4-only assumptions in generic computing primitives. | |

### Dimension Strategy
----
RID: `req-computing-core-dimensions`

Status: `Proposed`

Every TAP-managed type in the plugin uses meaningful `tap.computing` default dimensions, and the plugin experiments with explicit dimension nodes to document those categories.

#### Implementation

The plugin uses `tap.computing` as its core domain dimension key. Each model and edge type should declare a category value meaningful to the part of the computing stack it represents, for example:

- `host`
- `runtime`
- `storage`
- `network`
- `protocol`
- `identity`

These values should remain small, reviewable, and durable in v0. The purpose is not to create a deep ontology on day one, but to force the plugin to locate each type within the computing domain explicitly.

The plugin also experiments with explicit dimension nodes representing those categories, including explanatory descriptions of what each category means and why it exists. This is intended as a practical trial of TAP's optional dimension-node concept rather than a claim that the full dimension-node design is complete.

##### Web-Native Marker (future `web_core` seam)
----
RID: `req-computing-core-web-marker`

The `web_host` and `web_document` types were added under demo-time scope creep
above the plugin's intended "below service/application" line. To keep that
creep cleanly reversible, every web-native type and edge carries a second
dimension `tap.web: native` alongside its `tap.computing` stack-layer value.
This is an explicit future seam: a later `web_core` plugin can lift every
web-native type and edge in one shot by matching on the `tap.web` key, without
having to disentangle them from the genuine computing primitives. `tap.web`
also previews that plugin's eventual domain dimension key.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-dimensions-1 | Default Dimensions Required | Proposed | Each model declares meaningful `DEFAULT_DIMENSIONS` using the `tap.computing` key. | |
| req-computing-core-dimensions-2 | Edge Default Dimensions Required | Proposed | Each edge definition declares meaningful `default_dimensions` using the `tap.computing` key. | |
| req-computing-core-dimensions-3 | Small Category Set | Proposed | v0 uses a small, reviewable set of `tap.computing` values rather than ad hoc proliferation. | |
| req-computing-core-dimensions-4 | Dimension Node Experiment | Proposed | The plugin seeds dimension nodes explaining the chosen categories and their intent. | |
| req-computing-core-web-marker-1 | Web-Native Dual Tag | Proposed | `web_host`/`web_document` and their edges carry `tap.web: native` alongside their `tap.computing` value, so a future `web_core` split is a one-shot lift by `tap.web`. | |

#### Open Questions

Should `tap.computing` values be a tightly closed vocabulary enforced by validation, or should the plugin start with conventions only and tighten later once query patterns emerge?

### Model Catalog
----
RID: `req-computing-core-models`

Status: `Proposed`

The plugin declares vendor-neutral TAP-managed models organized by compute, runtime, storage, and networking concerns.

#### Implementation

The initial v0 model set is:

| Category | Models | Notes |
| --- | --- | --- |
| Compute | `host` (built); `virtual_machine`, `container` (planned) | The OS-bearing environment; physical versus virtual is `host.form_factor` (see [Host](#host)). The planned rows return only as specialisations a consumer needs |
| Runtime | `operating_system`, `program`, `process` | Operating context plus executable/runtime units |
| Storage | `storage_volume`, `filesystem`, `file` | Generic storage abstraction plus mounted and contained data |
| Networking | `network_interface`, `ip_address`, `ip_subnet`, `port` | Stable IP-stack primitives |
| Transport/Protocol | `tcp_connection`, `application_protocol` | Session node plus protocol abstraction above layer four |
| Identity | `user` | The human actor who interacts with the systems. **Ruled for retirement 2026-09-24 (Q60): `identity_core__human` is the person.** Retirement waits on its one consumer, tap-plugin-samsite (see below) |
| Web (web-native) | `web_host`, `web_document` | Internet hosts and URL-addressed documents; carry the `tap.web` marker (see below) |

Definitions and intent:

- **virtual_machine**: a guest compute environment managed above physical hardware
- **container**: a containerized execution environment
- **operating_system**: the OS environment associated with a virtual machine or container host
- **program**: the execution of an application concept that may spawn multiple processes and rely on executable/configuration/data files
- **process**: a concrete runtime process
- **storage_volume**: a generic storage backing unit such as a block-backed logical volume
- **filesystem**: a mounted or mountable filesystem namespace
- **file**: a filesystem object tracked as a durable artifact when meaningful
- **network_interface**: an operating-system-level interface such as `eth0`, `eth1`, or virtual equivalents
- **ip_address**: a generic IPv4 or IPv6 address
- **ip_subnet**: a generic IPv4 or IPv6 subnet or prefix
- **port**: a transport endpoint identified primarily by port number and transport family
- **tcp_connection**: a TCP session represented as a node
- **application_protocol**: a generic protocol concept that rides above transport and can later branch into specific protocols
- **host**: an environment that runs an operating system and executes programs — an end-user device, a server, a virtual machine, a container or a CI runner. See [Host](#host).
- **user**: a human who interacts with the systems; the generic person primitive. Roles such as administrator are expressed as assigned relationships rather than distinct node types, so a single `user` type can carry any edge in or out.
- **web_host**: a named internet host that serves content over HTTP(S), identified by hostname (e.g. `cisa.gov`). For external/unmanaged hosts this models the serving origin, not its internal compute.
- **web_document**: a document retrievable at a URL over HTTP(S) (e.g. the CISA KEV catalog). Distinct from `file`, which is a filesystem object keyed by path; a web document is network-delivered content addressed by URL.

Relationship simplification for v0:

- `program` runs on `operating_system`
- `operating_system` runs on `virtual_machine` or `container`

This is intentionally simpler than trying to model every possible runtime or orchestration path on the first pass.

**The person is `identity_core__human`.** `user` duplicates identity_core's human, which every system's account already resolves to with `HELD_BY_HUMAN__identity_core`; George ruled on 2026-09-24 (Q60) to keep `identity_core__human` and retire `user`. New work targets the human (`ASSIGNED_TO_HUMAN`, below) and never `user`. The model is not yet removed because a consumer outside this plugin still names it: tap-plugin-samsite seeds `computing_core__user` nodes (`grift/users.grift.json`), matches them in its landing search (`grift/landing.grift.json`) and selects them in `static/samsite/js/projections/landing-finalize.js`. Removing the type first would break that seed. The order is: samsite moves to `identity_core__human`, then a migration here deletes `user`. A machine-local account ("a Linux user": an OS login on a host) is a different concept from both, not built; identity may cover it later.

No type carries a free-form `configuration` field. Eight types (`network_interface`, `ip_address`, `port`,
`tcp_connection`, `program`, `file`, `public_key`, `private_key`) had one from the July 2026 monorepo
extraction, but no collector fills it, and a verbatim record with no reader is only a place for secret
material (a private key's, a config file's contents) or personal data to collect, so only promoted columns
are stored. Migration `0004_drop_unused_configuration` removed it.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-models-1 | Generic Primitive Set | Proposed | v0 declares a vendor-neutral set of computing primitives rather than provider-native resources. | |
| req-computing-core-models-2 | Program Included | Proposed | The model set distinguishes `program` from `process` and leaves higher-level `application` semantics deferred. | |
| req-computing-core-models-3 | Storage Volume Included | Proposed | The model set includes a generic `storage_volume` abstraction to support later provider integration. | |
| req-computing-core-models-4 | Application Deferred | Proposed | The plugin does not define a generic `application` or `service` model in v0. | |
| req-computing-core-models-5 | User Is Generic Person | Deprecated | The plugin models a generic `user` person type; roles such as administrator are assigned relationships, not distinct node types. | `tap.computing: identity`. Superseded 2026-09-24 (Q60) by `identity_core__human`; removal waits on tap-plugin-samsite. |
| req-computing-core-models-6 | Web-Native Primitives | Proposed | The plugin models `web_host` (internet host serving over HTTP(S)) and `web_document` (URL-addressed document), distinct from `file`. Both carry the `tap.web` marker. | Demo-time scope creep above the vendor-neutral line; see `req-computing-core-web-marker`. |
| req-computing-core-models-7 | No Free-Form Record | Implemented | No type declares `configuration`, and a `create_node` write carrying it is refused. | `tests/test_no_free_form_record.py` |

#### Open Questions

- Whether `operating_system` should represent a concrete installed OS instance, an OS family/version descriptor, or support both patterns may need additional design work during implementation.
- Whether `container` should always imply an underlying operating-system context directly or only through its host/runtime environment may need refinement once real container observations are modeled.

### Port Modeling
----
RID: `req-computing-core-ports`

Status: `Proposed`

Ports are first-class nodes whose primary identity is transport plus port number.

#### Implementation

The important durable field on a port is its port number. In v0, the plugin should support:

- well-known and registered server-side ports
- client-side ephemeral or unknown ports: the *unknown number* is `port_number = null` (grid convention); the *ephemeral signal* (number unknown but known to be ephemeral) is a separate observation, deferred to a future `is_ephemeral`/`role` field rather than overloaded onto `null` or a sentinel — see Future
- a simple port state field distinct from the numeric port identity

The v0 port state vocabulary should stay intentionally small:

- `listening`
- `bound`
- `connected`
- `closed`

This avoids overloading the port number while leaving room to express whether a port is merely bound, actively listening, or participating in a connection.

Ports should support more than one observational shape in v0:

- a structural shape where a port is attached to a known network interface
- an observational shape where a port is known to be available at an IP address even when the interface is not known

This is important because some data sources, such as network scanners, may observe only an IP address, port, and program path. The model should allow those observations without forcing creation of pseudo, assumed, or unknown network-interface nodes.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-ports-1 | Port Node Exists | Proposed | Ports are modeled as nodes, not only as integers embedded in other records. | |
| req-computing-core-ports-2 | Ephemeral Convention | Proposed | `port_number = null` means the port number is unobserved. The ephemeral/client-role signal is carried by a separate (future) `is_ephemeral`/`role` field, not overloaded onto `null`; "match any port" is a rule concept, out of scope for observation Port nodes. | Applies grid `req-grid-node-observation` (`null` = unobserved); see Future. |
| req-computing-core-ports-3 | Separate Port State | Proposed | Port state is modeled separately from the port number. | |
| req-computing-core-ports-4 | Interface Optional For Observation | Proposed | A port may be related directly to an IP address even when no concrete network interface is known. | |

#### Future
- **Ephemeral / role signal (`is_ephemeral` or `role`).** Disentangle the pre-convention `port_number = null` overload (originally "wildcard / ephemeral / unknown"). Under the grid convention `null` means only *number unobserved*; the positive fact "this is a client-side ephemeral port" — true even when the number is unknown — belongs in its own field. Add a nullable `is_ephemeral` boolean, or a richer `role` enum (`client` / `server` / `listening`) with ephemerality derivable, deciding bool-vs-role when built. The new field follows the grid field-observation convention itself (nullable = unobserved, carrying its own `x-tap-absence`). "Match any port" wildcard semantics, if ever needed, live on a rule/policy node, not on an observed Port. Named, not built.

### Network Interface Modeling
----
RID: `req-computing-core-interface`

Status: `Proposed`

A `network_interface` models an operating-system-level interface (`eth0`, a virtual equivalent). Its hardware address is carried by `mac_address`, which is a concrete application of the grid-wide field-observation convention (`tap_grid` `req-grid-node-observation`): a data source may observe an interface without its MAC — a scanner that sees the interface name but never captures the hardware address — so the field uses `mac_address = null` to mean **"hardware address unobserved or not applicable"**, distinct from `""`. This is the same convention `port_number = null` applies (`req-computing-core-ports-2`); both defer to the grid requirement for the full taxonomy, the FLIP known-vs-unknown-unknown hinge, and the lint-deviation rule.

`null` is therefore the deliberate "unobserved" representation for `mac_address` specifically; the interface's other string fields (`name`, `state`) use `default=""` because their empty case is a genuine empty string, not an unobserved one. The absence semantics are **declared**, not merely commented: `FIELD_CRUD_SCHEMA["mac_address"]["x-tap-absence"]` carries `null_default`, `empty_is_meaningful`, a `description`, and a Phase-2-reserved `not_applicable` clause (`permitted: true` — a loopback/virtual interface has no MAC by nature), and auto-publishes through `SERVICE_CRUD_SCHEMA` to external readers and Gryphon (grid `req-grid-node-observation-6`). Per the grid convention's DJ001 rule, the model field also carries `# noqa: DJ001  (req-computing-core-interface-1)` as the lint-silencer; the `x-tap-absence` annotation is the authoritative source of truth.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-interface-1 | MAC Unobserved Convention | Proposed | `mac_address = null` represents an interface whose hardware address was not observed or is not applicable, distinct from `""`. | Applies grid `req-grid-node-observation`; authorizes the model's `# noqa: DJ001  (req-computing-core-interface-1)`. |

### TCP Connection Modeling
----
RID: `req-computing-core-tcp`

Status: `Proposed`

TCP connections are modeled as nodes rather than direct edges.

#### Implementation

A TCP connection is represented as a node so TAP can attach:

- connection lifecycle state
- timing and observation metadata
- explanatory and dependency edges
- higher-layer protocol relationships

Edges are created in the direction of session creation:

- client port to TCP connection node
- TCP connection node to server port

This allows an `application_protocol` node to express that it relies on a specific TCP connection without collapsing transport and application flow into a single edge.

The v0 TCP connection state vocabulary should align with the classic RFC 793 lifecycle states rather than port states.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-tcp-1 | Connection Is Node | Proposed | A TCP connection is represented as a node. | |
| req-computing-core-tcp-2 | Directional Session Edges | Proposed | Session edges go from the client side to the connection node and from the connection node to the server side. | |
| req-computing-core-tcp-3 | Connection State Separate | Proposed | TCP lifecycle state lives on the connection, not on the port. | |
| req-computing-core-tcp-4 | Protocol Attachment Point | Proposed | Higher-layer protocol nodes may attach to the TCP connection node. | |

#### Future

Consider a future `udp_flow` model if real use cases emerge, and consider whether any later `ip_flow` concept should share that modeling direction. Deeper packet-hop or path modeling is intentionally deferred until TAP has a concrete need and a stable semantics for representing network hops.

### Protocol Scope
----
RID: `req-computing-core-protocols`

Status: `Proposed`

v0 stops just above layer four and does not yet commit to concrete application protocols.

#### Implementation

The plugin includes a generic `application_protocol` model as the jump-off point for later work, but it does not yet define dedicated models for HTTP, HTTPS/TLS, DNS, SSH, or similar protocols.

This keeps the plugin usable for connection and dependency modeling without forcing premature protocol taxonomy decisions.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-protocols-1 | Generic Protocol Model | Proposed | The plugin includes a generic `application_protocol` model. | |
| req-computing-core-protocols-2 | Concrete Protocols Deferred | Proposed | Specific protocols are deferred from v0. | |

### Edge Types
----
RID: `req-computing-core-edges`

Status: `Proposed`

The plugin favors a small but expressive edge family over generic catch-all edges.

#### Implementation

> **Candidate set pruned (pre-eviction, 2026-07-08).** These are aspirational candidate
> edge types, not a built inventory. Seven scaffolded-but-never-emitted edge definitions
> (`HOSTS`, `RUNS_ON`, `HAS_IP`, `AVAILABLE_AT`, `LISTENS_ON`, `CONNECTS_TO`, `PAIRED_WITH`)
> were deleted rather than frozen into the release tag as speculative surface. The only
> edges computing_core actually ships today are the ones consumers emit / seed:
> `FETCHES_DOCUMENT`, `GENERATES_FILE`, `HOSTS_DOCUMENT`. The candidates below return — correctly named
> per the add-edge skill — when a collector actually emits them.
>
> **Host edges built 2026-09-24.** `ASSIGNED_TO_HUMAN` and `REPRESENTS_HOST` ship with the `host`
> model; see [Host Edges](#host-edges).
>
> **Renamed 2026-09-10 (computing-core#4).** `HOSTED_BY` (document -> host) is now
> `HOSTS_DOCUMENT` (host -> document — the host is the actor, so the direction flipped) and the
> bare verb `FETCHES` is now `FETCHES_DOCUMENT`; both failed core's edge-naming check
> (`req-tap-plugin-edge-naming`: trailing preposition, bare verb) and were renamed rather than
> baselined. Migration `0003_retire_renamed_edge_types` deletes rows of the retired types on an
> upgraded grid; the next collection / seed re-emits them under the new names. Consumers
> (samsite's KEV seed + collector) move in their own follow-on.

Representative relationship categories for v0 include:

| Category | Candidate Edge Types | Description |
| --- | --- | --- |
| Structural | `HOSTS`, `RUNS_ON`, `CONTAINS`, `MOUNTS`, `BACKS`, `ATTACHED_TO` | Containment, hosting, and attachment relationships |
| Runtime | `EXECUTES`, `SPAWNS`, `LISTENS_ON`, `CONNECTS_TO` | Runtime execution and endpoint/session relationships |
| Networking | `HAS_IP`, `AVAILABLE_AT`, `BELONGS_TO_SUBNET`, `ROUTES_VIA` | Interface and address relationships, including scanner-visible observations |
| Protocol | `USES_PROTOCOL`, `RELIES_ON_CONNECTION` | Protocol attachment and dependency |
| Web (web-native) | `HOSTS_DOCUMENT`, `FETCHES_DOCUMENT` | A `web_host -HOSTS_DOCUMENT-> web_document`; any fetcher `-FETCHES_DOCUMENT-> web_document`. Both carry the `tap.web` marker. |

`FETCHES_DOCUMENT` deliberately leaves its source type as wildcard so any fetcher (a CI
workflow, a program) can fetch a `web_document` without `computing_core`
depending on the fetcher's owning plugin — e.g. a `github_workflow` (github_core)
fetching the CISA KEV catalog. The instance wiring lives with the consumer. It takes no
`_FROM`: the target IS the document fetched, not its origin (the skill's `PULLS_IMAGE`
shape, not `RETRIEVES_CONTENT_FROM`).

The exact edge set should remain expressive and specific enough that graph queries read naturally. Reuse matters, but v0 should lean toward semantic clarity rather than collapsing too much behavior into generic edges.

The initial networking shape should support both structural and scanner-visible views:

- `program -LISTENS_ON-> port`
- `port -ATTACHED_TO-> network_interface`
- `port -AVAILABLE_AT-> ip_address`
- `network_interface -HAS_IP-> ip_address`

This allows TAP to represent:

- a richer host-centric view when interfaces are known
- a thinner externally observed view when only IP, port, and program information are available

`AVAILABLE_AT` should not require `ATTACHED_TO` to exist. `HAS_IP` is the stronger structural claim when a concrete interface is known.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-edges-1 | Expressive Edge Family | Proposed | The plugin uses a small expressive edge family rather than relying primarily on generic reusable edges. | |
| req-computing-core-edges-2 | Session Directionality | Proposed | Edge naming and direction preserve the intended client-to-server session semantics. | |
| req-computing-core-edges-3 | Dimensioned Edges | Proposed | Every declared edge type carries meaningful `tap.computing` default dimensions. | |
| req-computing-core-edges-4 | Scanner Visible Port Shape | Proposed | The edge model supports port-to-IP observations without requiring a network interface node. | |
| req-computing-core-edges-5 | Program To Port Listening | Proposed | The model expresses that a program listens on a port independently of whether interface details are known. | |

#### Open Questions

The precise boundary between "expressive enough" and "too many unique edge types" should be revisited once the first real computing graphs are queried in practice.

Should `AVAILABLE_AT` be interpreted strictly as an observed externally reachable binding, or should it also cover local-only availability claims from host telemetry sources? v0 can start broad, but future protocol and perspective work may want a sharper distinction.

### Reference Data
----
RID: `req-computing-core-reference`

Status: `Proposed`

The plugin may seed small but useful generic reference data.

#### Implementation

The first reference-data candidate is dimension nodes for the `tap.computing` category values used by the plugin. Those nodes should describe what each category means and why it exists.

The plugin may later seed small generic vocabularies such as TCP states or protocol categories if doing so proves useful, but v0 should stay conservative and avoid creating taxonomy data without a concrete graph use case.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-reference-1 | Dimension Nodes Seeded | Proposed | The plugin seeds dimension nodes describing the chosen `tap.computing` categories. | |
| req-computing-core-reference-2 | Minimal Reference Surface | Proposed | v0 seed data stays small and justified by actual graph use. | |

### Plugin Validation
----
RID: `req-computing-core-validation`

Status: `Proposed`

The plugin should pass TAP's centralized plugin validation system and encourage deeper validation before public release.

#### Implementation

The plugin should pass:

- `structure` validation during early authoring
- future `loads` and `runs` validation before the plugin is considered ready for broader publication

This matters especially for a plugin with many concrete models, where importability alone does not prove that migrations, tables, and runtime behavior are sound.

#### Acceptance Criteria

| ACID | Title | Status | Description | Notes |
| --- | --- | :---: | --- | --- |
| req-computing-core-validation-1 | Structure Validation Required | Proposed | The plugin must pass TAP plugin structure validation. | |
| req-computing-core-validation-2 | Deeper Validation Recommended | Proposed | Authors should run future `loads` and `runs` validation before publishing the plugin widely. | |

### v0 Non-Goals
----
RID: `req-computing-core-nongoals`

Status: `Proposed`

This specification does not define:

- physical hardware modeling
- cloud-provider-native resource types
- packet-level or hop-level network modeling
- UDP or IP flow modeling
- concrete application-protocol models such as HTTP, DNS, or TLS
- generic `service` or `application` models
- cross-plugin dependency contracts, beyond the one vocabulary dependency on identity_core that `ASSIGNED_TO_HUMAN` needs ([Host Edges](#host-edges))

These are important future concerns, but they are intentionally outside the first Computing Core pass.

## Future Work

- Split networking and protocol concerns into dedicated plugins if the graph grows deep enough to justify that boundary.
- Add richer protocol models above `application_protocol`.
- Add `udp_flow` if real use cases justify it.
- Explore packet-hop or path modeling when TAP has a stable need to reason about concrete network hops.
- Define a clearer relationship between `program`, `process`, and any future `application` or `service` concepts.
