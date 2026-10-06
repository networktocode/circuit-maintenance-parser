# v2.11 Release Notes

This document describes all new features and changes in the `2.11` release series. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.11.0 (2026-04-15)](https://github.com/networktocode/circuit-maintenance-parser/releases/tag/v2.11.0)

### Added

- [#375](https://github.com/networktocode/circuit-maintenance-parser/issues/375) - Added Google subject parser with support for multiple status types and notifications without end times.

### Fixed

- [#372](https://github.com/networktocode/circuit-maintenance-parser/issues/372) - Refactored OpenAI parser to be used as a fallback and fixed subject injection to skip text/calendar parts.
- [#377](https://github.com/networktocode/circuit-maintenance-parser/issues/377) - Fixed Lumen parser incorrectly marking scheduled future maintenance events as IN-PROCESS instead of CONFIRMED. Bug introduced in commit 737aa4e9 (Aug 2021).

### Dependencies

- [#391](https://github.com/networktocode/circuit-maintenance-parser/issues/391) - Upgraded lxml to version 6.0.2 and normalized CRLF line endings in HTML parser output.
- [#393](https://github.com/networktocode/circuit-maintenance-parser/issues/393) - Pinned lxml version to support >=4.6.2,<7.

### Housekeeping

- [#384](https://github.com/networktocode/circuit-maintenance-parser/issues/384) - Added Python 3.13 to supported versions and CI matrix.
- Added required cookiecutter json file for drift management setup.
- Fixed incorrectly set cookiecutter project_slug.
