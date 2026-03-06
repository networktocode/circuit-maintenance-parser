# Library Overview

This document provides an overview of the library including critical information and important considerations.

## Description

`circuit-maintenance-parser` is a Python library that parses circuit maintenance notifications from Network Service Providers (NSPs), converting heterogeneous formats to a well-defined structured format.

Every network depends on external circuits provided by NSPs who interconnect them to the Internet, to office branches or to external service providers such as Public Clouds. These services occasionally require operation windows to upgrade or fix related issues, usually in the form of **circuit maintenance periods**. NSPs generally notify customers of these upcoming events so that customers can take actions to minimize impact.

The challenge is that almost every NSP defines its own maintenance notification format, even though the relevant information is mostly the same. This library parses notification formats from several providers and returns a standardized object struct, making it easier to process them.

The output format follows the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) defined during a NANOG meeting that promotes the usage of the iCalendar format.

## Audience (User Personas) - Who should use this Library?

- **Network Engineers** who need to automate the processing of circuit maintenance notifications from multiple providers.
- **Network Operations Center (NOC) teams** who want to standardize how maintenance windows are tracked across different NSPs.
- **Automation developers** building workflows that need to programmatically consume and act on circuit maintenance notifications.

## Authors and Maintainers

This library is maintained by [Network to Code](https://www.networktocode.com/). For a full list of contributors, see the [GitHub contributors page](https://github.com/networktocode/circuit-maintenance-parser/graphs/contributors).
