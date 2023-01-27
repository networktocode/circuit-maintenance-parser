# Changelog

## v2.2.2 - 2023-01-27

### Changed

- #204 - Updated pydantic version support

## v2.2.1 - 2023-01-17

### Changed

- #197 - Updated Equinix parser: Adding support for additional impact statement and notification types.
- #192 - Updated Cogent parser: Adding subject and text parser.
- #186 - Updated Telia Carrier as Arelion (while keeping Telia for backwards compatibility).

### Fixed

- #198 - Fixed Verizon parser: use European-style day-first date parsing
- #187 - Fixed Zayo parser: adds chardet.detect method before decoding data_part.content.

## v2.2.0 - 2022-10-25

### Added

- #169 - Add a helper script to anonymize IP addresses using `netconan`
- #163 - New parser for BSO provider

### Changed

- #182 - Moved `toml` to dev-dependencies
- #181 - Changed mypy to v0.982
- #180 - **Minimum Python version changed** from `3.6.2` to `3.7`
- #179 - Do not require an "[ EXTERNAL ]" marker for Colt email subjects
- #176 - Handle Zayo table with "Customer Circuit ID" header
- #170 - Update networktocode/gh-action-setup-poetry-environment action to v4
- #164 - Improve CI concurrency
- #161 - Update dependency flake8 to v5
- #160 - Update slackapi/slack-github-action action to v1.23.0
- #154 - Do not accept `pydantic` v1.9.1
- #151 - Changed version `types-pytz` to v2022
- #150 - Update actions/setup-python action to v4
- #148 - Update actions/checkout action to v3
- #147 - Update slackapi/slack-github-action action to v1.19.0
- #146 - Migrate CI from Travis to Github Actions
- #138 - Update dependency pytest to v7

### Fixed

- #177 - Fixed Colt parser: use European-style day-first date parsing

## v2.1.0 - 2022-05-13

### Changed

- #143 - Minimum Python version changed from `3.6.1` to `3.6.2`

### Fixed

- #132 - Handle alternate "has been cancelled" text in Telstra notifications.
- #134 - Handle Zayo "RESCHEDULE" notifications.
- #143 - Fix Equinix parser not taking year into account

## v2.0.8 - 2021-12-09

### Fixed

- #115 - Add default `status` and `sequence` values for iCal notifications missing these fields
- #124 - Handle encoded non-ASCII characters in email subjects.
- #126 - Ignore a class of non-maintenance-notification emails from Telia.
- #127 - Improve handling of Equinix and Lumen notifications.
- #128 - Add capability to set `RE-SCHEDULED` status for Verizon rescheduled notifications.

## v2.0.7 - 2021-12-01

### Fixed

- #120 - Improve handling of Zayo notifications.
- #121 - Defer loading of `tzwhere` data until it's needed, to reduce memory overhead.

## v2.0.6 - 2021-11-30

### Added

- #116 - New `EmailSubjectParser` for Colt notifications and tests.
- #117 - Add new notification status of `Alternate Night` for Lumen.

## v2.0.5 - 2021-11-18

### Fixed

- #109 - Improve handling of Zayo notifications.
- #110 - Improve handling of Telstra notifications.
- #111 - Improve handling of EXA (GTT) notifications.
- #112 - Improve handling of Equinix notifications.

## v2.0.4 - 2021-11-04

### Fixed

- #94 - Improve Geo service error handling.
- #97 - Fix Readme image URLs.
- #98 - Add handling for `Lumen` notification with Alt Circuit ID.
- #99 - Extend `Zayo` Html parser to handle different table headers.
- #102 - Add `Equinix` provider.
- #104 - Use a local locations DB to map city to timezone as first option, keeping API as fallback option.
- #105 - Extend `Colt` parser to support multiple `Maintenance` statuses.

## v2.0.3 - 2021-10-01

### Added

- #84 - New parser added for text. Added new provider `AWS` using `Text` and `EmailSubjectParser`
- #91 - `Provider` now adds `_include_filter` and `_exclude_filter` attributes (using regex) to filter in and out notifications that are relevant to be parsed vs other that are not, avoiding false positives.

### Fixed

- #90 - Improved handling of Lumen scheduled maintenance notices

## v2.0.2 - 2021-09-28

### Fixed

- #86 - Fix `CombinedProcessor` carries over data from previous parsing

## v2.0.1 - 2021-09-16

### Fixed

- #79 - Fix `HtmlParserGTT1` regex parsing.

## v2.0.0 - 2021-09-15

### Added

- #73 - Added new provider `Sparkle` using `Html` and `EmailSubjectParser`. Added support for multiple maintenances with `CombinedProcessor`.
- #75 - Added new provider `AquaComms` using `Html` and `EmailSubjectParser`

### Fixed

- #72 - Ensure `NotificationData` init methods for library client do not raise exceptions and just return `None`.

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
- #68 - Added new provider `HGC` using `Html` and `EmailSubjectParser`

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
