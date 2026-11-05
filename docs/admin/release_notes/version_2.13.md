# v2.13 Release Notes

This document describes all new features and changes in the `2.13` release series. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Release Overview

- Added parsers for three new providers: Comcast Business, Hawaiki and KPN.
- Extended existing parsers: Telxius cancelled maintenance notices are now recognized, and the SummitIG parser accepts times in UTC.
- Widened the supported ranges of `icalendar` (<8), `chardet` (<8), `timezonefinder` (<10), `python-dateutil` (<4) and `pandas` (<4) so the library installs alongside their latest major versions. Minimum versions are unchanged, so existing environments do not need to upgrade.
- Declared `pytz` as a direct dependency, since newer `icalendar` releases no longer install it.
- Supported Python versions are unchanged (3.10 through 3.14).

<!-- towncrier release notes start -->

## [v2.13.0 (2026-11-03)](https://github.com/networktocode/circuit-maintenance-parser/releases/tag/v2.13.0)

### Security

- [#439](https://github.com/networktocode/circuit-maintenance-parser/issues/439) - Updated dependency `geopy` to `^2.5.0` to mitigate GHSA-mhvh-fq92-pfmr.
- [#440](https://github.com/networktocode/circuit-maintenance-parser/issues/440) - Updated dependency `urllib3` to `>=2.8.0,<3.0.0` to mitigate CVE-2026-97688.

### Added

- [#429](https://github.com/networktocode/circuit-maintenance-parser/issues/429) - Added Hawaiki provider, parser and tests.
- [#432](https://github.com/networktocode/circuit-maintenance-parser/issues/432) - Added KPN provider, parser and tests.
- [#436](https://github.com/networktocode/circuit-maintenance-parser/issues/436) - Added support for the UTC timezone in the SummitIG parser.
- [#443](https://github.com/networktocode/circuit-maintenance-parser/issues/443) - Added a parser for Comcast Business maintenance notifications.

### Fixed

- [#435](https://github.com/networktocode/circuit-maintenance-parser/issues/435) - Added support for Telxius cancelled maintenance notices.

### Dependencies

- Widened the `icalendar`, `chardet`, `timezonefinder`, `python-dateutil` and `pandas` ranges to allow their latest major versions, and refreshed development and documentation dependencies including ruff 0.17, griffe 1.15, invoke 3 and towncrier 26.
- Declared `pytz` as a direct dependency, since the library imports it and newer `icalendar` releases no longer install it.

### Housekeeping

- [#437](https://github.com/networktocode/circuit-maintenance-parser/issues/437) - Updated development dependency `mkdocs-material` to `9.7.7` to mitigate CVE-2026-73295.
- Rebaked from the cookie `main`.
- Refreshed the lock file to resolve open Dependabot advisories for `certifi`, `idna`, `soupsieve`, `anyio` and `pymdown-extensions`.
