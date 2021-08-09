# Changelog

## v1.2.2 -

### Added

- #41 - Added new provider `Telia` using `Ical`
- #42 - Improve error and debug messages to ease troubleshooting of parsing issues

## v1.2.1 - 2021-06-22

### Fix

- #32 - Fix backwards compatibility with version 1.1.0 that was broken in 1.2.0
- #31 - Fix consistent provider (and other attributes) usage in all the classes

## v1.2.0 - 2021-06-21

### Added

- #25 - added **Cogent** parser
- #26 - Multiple Parsers per Provider, even combining ICal with custom HTML.

## v1.1.0 - 2021-06-09

### Added

- #16 - changed `MaintenanceNotification.raw` from `str` to `bytes`, improve **Zayo** parser, and add -v/--verbose CLI option
- #17 - added **Lumen** parser and refactor HTML parser `process` method
- #18 - added **Telstra** parser and made `Maintenance.stamp` attribute optional
- #19 - added **Megaport**

### Fixes

- #15 - Update Pydantic version due to security advisory GHSA-5jqp-qgf6-3pvh

## v1.0.2 - 2021-05-05

### Added

- #10 - added `cli` command to run as a script

## v1.0.0 - 2021-04-29

Initial release
