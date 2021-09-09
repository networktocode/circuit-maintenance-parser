# Changelog

## v2.0.0 - 

### Added

- #68 - Added new provider `HGC` using `Html` and `EmailSubjectParser`

## v2.0.0-beta - 2021-09-07

### Added

- #50 - Added new provider `Verizon` using `Html`
- #52 - Added new provider `GTT` using `Html`
- #53 - `circuit-maintenace-parser` refactor, including:
  - New `Processor` class that allows the `Provider` to define more custom logics to combine parsed data to create
    `Maintenances`
  - New `NotificationData` class that enables easier data injection for simple and complex data objects, such as
    emails.
  - Tests refactor to make them more specific to each type of data, mocking interfaces between different classes.
- #54 - Added new provider `Turkcell` using `Html`
- #59 - Added a new parser `EmailDateParser` that uses the temail `Date` to get the `Stamp` and use in most of the `Providers` via the `CombinedProcessor`. Also, `Maintenance.stamp` attribute is mandatory.
- #60 - Added new provider `Seaborn` using `Html` and a new parser for Email Subject: `EmailSubjectParser`
- #61 - Added new provider `Colt` using `ICal` and `Csv`
- #66 - Added new provider `Momentum` using `Html` and `EmailSubjectParser`

### Fixed

- #49 - Improved `Lumen` `Html` parsing.

## v1.2.3 - 2021-08-12

### Fixed

- #46 - Accept <8.0 Click version to avoid dependency issues with other client packages

## v1.2.2 - 2021-08-12

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
