# Changelog

## [0.10.8](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.7...v0.10.8) (2026-11-12)


### Features

* **computing_core:** declare the tap.computing.cloud dimension ([#81](https://github.com/unified-systems-com/computing-core-tap/issues/81)) ([e52d04e](https://github.com/unified-systems-com/computing-core-tap/commit/e52d04ef36ba5a9ee05039d7a5d38953514b3356))
* **computing_core:** network and loopback_address types; ip_address refuses host-scoped addresses ([#79](https://github.com/unified-systems-com/computing-core-tap/issues/79)) ([a975736](https://github.com/unified-systems-com/computing-core-tap/commit/a97573684cc3150b70f7f1ccdb96fc42abb4967d))
* **computing_core:** seed the network_name, host and Kubernetes dimension nodes ([#80](https://github.com/unified-systems-com/computing-core-tap/issues/80)) ([0267195](https://github.com/unified-systems-com/computing-core-tap/commit/02671959252f3ec90ee4118f65141e6fa941f9b0))

## [0.10.7](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.6...v0.10.7) (2026-11-11)


### Features

* **kubernetes:** a namespace, a node and a pod keep their annotations ([18d932c](https://github.com/unified-systems-com/computing-core-tap/commit/18d932c96e74ad8e783b08ab9a34c313a634c233))
* **kubernetes:** a namespace, a node and a pod keep their annotations ([81ca92e](https://github.com/unified-systems-com/computing-core-tap/commit/81ca92e695d22c8349dc38829972a7d2b51b49d5))


### Bug Fixes

* **kubernetes:** refuse the annotation that holds a whole applied manifest ([4b5727d](https://github.com/unified-systems-com/computing-core-tap/commit/4b5727d0a996780384ff08173e83fc6a89f0e608))


### Documentation

* **kubernetes:** say which write path the annotation check covers ([7b2ef9c](https://github.com/unified-systems-com/computing-core-tap/commit/7b2ef9c5d1e9464c30969203b4801f7ec2eff517))

## [0.10.6](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.5...v0.10.6) (2026-11-11)


### Features

* **image:** generic image facts on the host, and an image tag type ([dc6a15f](https://github.com/unified-systems-com/computing-core-tap/commit/dc6a15f6c2239d783025529102f69d6400119523))
* **image:** generic image facts on the host, and an image tag type ([a13fa72](https://github.com/unified-systems-com/computing-core-tap/commit/a13fa720163fb6efea2479280c757f38f2b76600))


### Bug Fixes

* **image:** detected_at must be a date-time with a zone; a build time with no zone is refused as a datetime too ([7cc8644](https://github.com/unified-systems-com/computing-core-tap/commit/7cc864446ddb5acc7b33c5e3c83f93c0e863d4e0))


### Documentation

* **spec:** say what TAGS_IMAGE does not check ([0819908](https://github.com/unified-systems-com/computing-core-tap/commit/0819908ff58dca0b635b16aaa5420291204a5bfc))

## [0.10.5](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.4...v0.10.5) (2026-11-10)


### Features

* **sbom:** parse an unsigned document from an authenticated source, and never call it verified ([18e7987](https://github.com/unified-systems-com/computing-core-tap/commit/18e79872fb87d1bc57bd7d0deb4a1a5aff8df498))
* **sbom:** parse an unsigned document from an authenticated source, and never call it verified ([84609f8](https://github.com/unified-systems-com/computing-core-tap/commit/84609f824cbb56de177c16cf01a18f994eb6e959))


### Bug Fixes

* **sbom:** authenticated_source is in the validation schema beside signer and verification_note ([85cdc86](https://github.com/unified-systems-com/computing-core-tap/commit/85cdc864095d95a268951cc1a9036518a07e2c64))
* **sbom:** restore the Model Catalog the last commit deleted by mistake; a source is never only whitespace ([fca8292](https://github.com/unified-systems-com/computing-core-tap/commit/fca829276ca0016f2c7624602f81d6d0bf82bb24))


### Documentation

* **kubernetes:** the cluster name is the display name under any realm ([d542769](https://github.com/unified-systems-com/computing-core-tap/commit/d542769594d4ed901bd1e03a00bc2800519198f8))
* **spec:** a cluster realm for a name only one source configured ([7ab3a6b](https://github.com/unified-systems-com/computing-core-tap/commit/7ab3a6b4c8048372e86e35e023321536461fad23))
* **spec:** a cluster realm for a name only one source configured ([8e42daf](https://github.com/unified-systems-com/computing-core-tap/commit/8e42dafbf62ed161975cf398080507014a7ce726))
* **spec:** propose a source-authenticated SBOM outcome, for the maintainer to rule on ([1da8e04](https://github.com/unified-systems-com/computing-core-tap/commit/1da8e041863c20263f1743103b1b7ea2388accdd))
* **spec:** the document field table says which outcomes are parsed and how null is told apart ([e4511bb](https://github.com/unified-systems-com/computing-core-tap/commit/e4511bb0ee49e1965eb3ac53c6d1b42e69d8efe6))

## [0.10.4](https://github.com/unified-systems-com/computing-core-tap/compare/v0.10.3...v0.10.4) (2026-11-09)


### Features

* **kubernetes:** cluster, namespace, pod, node and container types with placement edges ([3ebd3b1](https://github.com/unified-systems-com/computing-core-tap/commit/3ebd3b1478de6c9c7f02033e180e0c739ef8e3c3))
* **kubernetes:** cluster, namespace, pod, node and container types with placement edges ([f9f0ae1](https://github.com/unified-systems-com/computing-core-tap/commit/f9f0ae12024bc8559c93a4c3e490dca8fe7b26f2))


### Bug Fixes

* **kubernetes:** nothing is contained by the cluster ([d4abd4e](https://github.com/unified-systems-com/computing-core-tap/commit/d4abd4e0e0c4ae62ce5c6c0378c6093796527c4d))
* **kubernetes:** say which types constrain inbound edges; test the uid-alone cost ([df3cc11](https://github.com/unified-systems-com/computing-core-tap/commit/df3cc1167a8941904493d5a9b8bdc15c29a0bbac))

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
