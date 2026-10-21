# Changelog

## [0.5.1](https://github.com/unified-systems-com/computing-core-tap/compare/v0.5.0...v0.5.1) (2026-10-21)


### Features

* application_flow node and APPLICATION_FLOW_SOURCE/DESTINATION, RUNS_PROGRAM, RUNS_IMAGE edges [via rampart-pg] ([#49](https://github.com/unified-systems-com/computing-core-tap/issues/49)) ([bf1c2d1](https://github.com/unified-systems-com/computing-core-tap/commit/bf1c2d10b040c5cf705e8d49a86a8d33eed3d82f))
* **computing_core:** RUNS_PACKAGE, USES_KEY and an operating system running a program ([0df4b62](https://github.com/unified-systems-com/computing-core-tap/commit/0df4b62f3da6b6cdb2fc41cd972fc772f250556d))
* **computing_core:** RUNS_PACKAGE, USES_KEY and an operating system running a program ([e59881e](https://github.com/unified-systems-com/computing-core-tap/commit/e59881e0dd5c540d99495e84287c2949d8a9b64d))
* **icons:** the application flow is a dark-blue circle icon, drawn as an ellipse ([#51](https://github.com/unified-systems-com/computing-core-tap/issues/51)) ([65b47fd](https://github.com/unified-systems-com/computing-core-tap/commit/65b47fd976319a956780d282402929e5f48de03d))
* **icons:** the host icon is a blue outline on white, not a dark tile ([#47](https://github.com/unified-systems-com/computing-core-tap/issues/47)) ([f632bc8](https://github.com/unified-systems-com/computing-core-tap/commit/f632bc8459636319fcc4139b77247eec5519d481))
* package, library, operating_system and crypto_provider types, with the inventory edges ([6903911](https://github.com/unified-systems-com/computing-core-tap/commit/69039114810d7d3d7d5e0c71fba1bc5cd86a2666))
* package, library, operating_system and crypto_provider types, with the inventory edges [via rampart-pg] ([4045148](https://github.com/unified-systems-com/computing-core-tap/commit/40451483868a2bf81f89ed2495846a41b04d43a7))
* **sbom_document:** verification_note names the failing check, current() is verified-only ([da86cfe](https://github.com/unified-systems-com/computing-core-tap/commit/da86cfe1cd808749e7b6fe0179323a243fba0ea7))
* **sbom:** parse_cyclonedx_vulnerabilities reads vulnerabilities[] of a verified SBOM [via rampart-pg] ([#45](https://github.com/unified-systems-com/computing-core-tap/issues/45)) ([93112fe](https://github.com/unified-systems-com/computing-core-tap/commit/93112febd66600d22672b816c06a588720ac82a5))
* **sbom:** pure CycloneDX parser and builder, tap-web SBOM corpus [via rampart-pg] ([9d2d3e3](https://github.com/unified-systems-com/computing-core-tap/commit/9d2d3e3e15cd2bde37f3565b9edbdd30a06d0f31))
* **sbom:** pure CycloneDX parser and builder, with the attested tap-web document as corpus ([5a95494](https://github.com/unified-systems-com/computing-core-tap/commit/5a95494d67f893c8b8afccd7423318fc9feac6ba))
* **sbom:** sbom_document node, REQUIRES_PACKAGE and DESCRIBES_HOST edges, package.cpe_candidates ([d45b1fd](https://github.com/unified-systems-com/computing-core-tap/commit/d45b1fd54f397729aba50fa405ffd5cd1fc8777e))
* **sbom:** sbom_document, REQUIRES_PACKAGE, DESCRIBES_HOST, package.cpe_candidates [via rampart-pg] ([1018d23](https://github.com/unified-systems-com/computing-core-tap/commit/1018d234f195f7e79478b61da9de848c24971e8c))
* **sbom:** verification outcome on the document row, record_document for a document that is not parsed ([9366331](https://github.com/unified-systems-com/computing-core-tap/commit/93663311a98f049bed66ffabd1e44977da9eacbf))
* source_package node and DERIVES_FROM_SOURCE_PACKAGE edge [via rampart-pg] ([90475ce](https://github.com/unified-systems-com/computing-core-tap/commit/90475cefe399a3fb46fd29c466513420e437f7ff))
* **source_package:** add source_package node and DERIVES_FROM_SOURCE_PACKAGE edge ([0c909de](https://github.com/unified-systems-com/computing-core-tap/commit/0c909de8c02b6304bcb285d9a54f141877f2477a))


### Bug Fixes

* **sbom_document:** bound every field to its column, validate produced_at, test that nothing may point at a document ([4761b87](https://github.com/unified-systems-com/computing-core-tap/commit/4761b87f22a83544c0ea18a24e717cfcc26dbad7))
* **sbom:** fail closed on every hostile shape, keep every value inside its column, harden the tests ([25801da](https://github.com/unified-systems-com/computing-core-tap/commit/25801dabb2f177b1b197aac0fc424d052e588a72))
* **sbom:** verification is required, record_document reads nothing, non-string specVersion is refused ([59e3436](https://github.com/unified-systems-com/computing-core-tap/commit/59e3436ac4f7e3dfcb3727c95f4f93a75af8767f))

## [0.5.0](https://github.com/unified-systems-com/computing-core-tap/compare/v0.4.0...v0.5.0) (2026-10-08)


### ⚠ BREAKING CHANGES

* computing_core__user no longer exists. samsite seeds it and pins <0.5. It moves to identity_core__human in unified-systems-com/samsite-tap#33.
* FETCHES_DOCUMENT__computing_core and HOSTS_DOCUMENT__computing_core no longer exist. samsite seeds HOSTS_DOCUMENT, emits FETCHES_DOCUMENT and draws HOSTS_DOCUMENT in its landing projection; it pins <0.5 and must move before taking 0.5.

### Features

* host, os_user and os_group; retire computing_core__user ([958aaee](https://github.com/unified-systems-com/computing-core-tap/commit/958aaee7ec26cb1ff3b207d607b78058b0cdf49e))
* retire FETCHES_DOCUMENT and HOSTS_DOCUMENT [via highbar] ([71be3ec](https://github.com/unified-systems-com/computing-core-tap/commit/71be3ec2b7653b52299dfad8d45a5f1abd741739))


### Bug Fixes

* **boot:** pin the commit beside every git source's rev in the CI record ([f0ce777](https://github.com/unified-systems-com/computing-core-tap/commit/f0ce777f8171b185c469b48508ebb28beee2716b))
* **boot:** pin the commit beside every git source's rev in the CI record [via bom-bom] ([7ded2ba](https://github.com/unified-systems-com/computing-core-tap/commit/7ded2bace4a59f64deeffd570ae79259c67b4430))
* **manifest:** raise the tap floor to 0.3.0 ([9c61074](https://github.com/unified-systems-com/computing-core-tap/commit/9c61074a08912bfa7d8cb657424a5c8ac8fc39d8))


### Documentation

* cite issues, not session rulings, in code and spec ([2b52adc](https://github.com/unified-systems-com/computing-core-tap/commit/2b52adce02fa296a64198f0440dcbd4d8846a24e))
* **models:** say plainly that a POSIX rename is a new os_user / os_group ([8ec1aa4](https://github.com/unified-systems-com/computing-core-tap/commit/8ec1aa48738dc9c13c893ee999c4ae1cc0e6cc0b))
