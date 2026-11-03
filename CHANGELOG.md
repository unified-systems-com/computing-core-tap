# Changelog

## [0.10.3](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.2...v0.10.3) (2026-11-03)


### Features

* **computing_core:** oci-digest realm for image hosts ([e14131b](https://github.com/unified-systems-com/computing-core-tap/commit/e14131be5e76135891c6ebcdc166674ccc2cde39))
* **computing_core:** oci-digest realm for image hosts ([ef04119](https://github.com/unified-systems-com/computing-core-tap/commit/ef04119f98bb14e25186055255f42c93d3ee0d13))
* **computing_core:** the module type and LOADS_MODULE, CONTAINS_MODULE, IMPORTS_MODULE ([a1f597b](https://github.com/unified-systems-com/computing-core-tap/commit/a1f597b4a7da96da8d7447651544b3402454ed80))
* **computing_core:** the module type and LOADS_MODULE, CONTAINS_MODULE, IMPORTS_MODULE ([6825a1d](https://github.com/unified-systems-com/computing-core-tap/commit/6825a1d78923371d16ca54c38b6e5d7e2d205408))


### Bug Fixes

* **manifest:** write plugin_version without the v prefix ([87b6d55](https://github.com/unified-systems-com/computing-core-tap/commit/87b6d55783c6bd334bf1ce657347e373a1fc0599))
* **manifest:** write plugin_version without the v prefix ([d345f10](https://github.com/unified-systems-com/computing-core-tap/commit/d345f108b1b3ebaecf6ff03e3d395dda3a9b8b97))
* **sbom-document:** accept any edge whose definition permits it, instead of none ([8c5dc18](https://github.com/unified-systems-com/computing-core-tap/commit/8c5dc180964b040d8ab3489fe8367909c1feb271))
* **sbom-document:** accept any edge whose definition permits it, instead of none ([ca60ed9](https://github.com/unified-systems-com/computing-core-tap/commit/ca60ed9bf65636d2b61eb0e518c45d901239f3cc))


### Documentation

* **spec:** the module type with a language, and its three edges ([443db91](https://github.com/unified-systems-com/computing-core-tap/commit/443db91decde614c79e75a5cc8bf7fe8381db4ce))

## [0.10.2](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.1...v0.10.2) (2026-10-21)


### Features

* **computing_core:** RUNS_PACKAGE, USES_KEY and an operating system running a program ([0df4b62](https://github.com/unified-systems-com/computing-core-tap/commit/0df4b62f3da6b6cdb2fc41cd972fc772f250556d))
* **computing_core:** RUNS_PACKAGE, USES_KEY and an operating system running a program ([e59881e](https://github.com/unified-systems-com/computing-core-tap/commit/e59881e0dd5c540d99495e84287c2949d8a9b64d))


### Bug Fixes

* **release:** set the release-please manifest to the released version, 0.10.1 ([45aad44](https://github.com/unified-systems-com/computing-core-tap/commit/45aad4428feb9f806888832a767a5fce2f9f0acf))
* **release:** set the release-please manifest to the released version, 0.10.1 ([90e2d1e](https://github.com/unified-systems-com/computing-core-tap/commit/90e2d1e53df8f27f9337d4f35e2677e5a9317895))

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
