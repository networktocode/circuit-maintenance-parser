# v2.12 Release Notes

This document describes all new features and changes in the `2.12` release series. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.12.0 (2026-06-12)](https://github.com/networktocode/circuit-maintenance-parser/releases/tag/v2.12.0)

### Security

- [#415](https://github.com/networktocode/circuit-maintenance-parser/issues/415) - Bumped `lxml` (>=6.1.0), `urllib3` (>=2.7.0), `requests` (>=2.33.0), and `pygments` (>=2.20.0) to address open Dependabot advisories (XXE in iterparse, sensitive-header forwarding on proxied redirects, decompression-bomb safeguard bypass, insecure temp file reuse, ReDoS).

### Added

- [#395](https://github.com/networktocode/circuit-maintenance-parser/issues/395) - Added parser for SummitIG.
- [#412](https://github.com/networktocode/circuit-maintenance-parser/issues/412) - Added parser for provider RETN.
- [#414](https://github.com/networktocode/circuit-maintenance-parser/issues/414) - Added parser for provider Telxius.
- [#416](https://github.com/networktocode/circuit-maintenance-parser/issues/416) - Added parser for Vodafone.
- [#417](https://github.com/networktocode/circuit-maintenance-parser/issues/417) - Added Cirion parser (Lumen fork).
- [#419](https://github.com/networktocode/circuit-maintenance-parser/issues/419) - Added parser for FLAG (fka Globalcloudexchange).

### Fixed

- [#378](https://github.com/networktocode/circuit-maintenance-parser/issues/378) - Fixed Megaport parser to account for initial and reminder announcements, corrected start and end dates for both, and fixed the "purpose of maintenance" section.
- [#411](https://github.com/networktocode/circuit-maintenance-parser/issues/411) - Fixed Equinix parser to match `maintenance_id` for the alternative email subject line, when the `maintenance_id` is not matched between square brackets.

### Dependencies

- [#415](https://github.com/networktocode/circuit-maintenance-parser/issues/415) - Bumped Python dependencies (click, coverage, netconan, pylint, ruff, cffi, pymdown-extensions) and CI action pins (actions/checkout, docker/setup-buildx-action, pypa/gh-action-pypi-publish).
- [#415](https://github.com/networktocode/circuit-maintenance-parser/issues/415) - Added Python 3.14 to the supported version range and split `numpy` by Python version (2.2.x on Python 3.10, >=2.3 on 3.11+) so the same lock resolves cleanly across the full supported range.

### Housekeeping

- [#396](https://github.com/networktocode/circuit-maintenance-parser/issues/396) - Raised the minimum pytest version to 9.0.3 to address CVE-2025-71176 (insecure /tmp/pytest-of-{user} tmpdir handling on UNIX).
- Rebaked from the cookie `main`.
