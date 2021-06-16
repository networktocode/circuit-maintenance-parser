# circuit-maintenance-parser

`circuit-maintenance-parser` is a Python library that parses circuit maintenance notifications from Network Service Providers (NSPs), converting heterogeneous formats to a well-defined structured format.

## Context

Every network depends on external circuits provided by NSPs who interconnect them to the Internet, to office branches or to
external service providers such as Public Clouds.

Obviously, these services occasionally require operation windows to upgrade or to fix related issues, and usually they happen in the form of **circuit maintenance periods**.
NSPs generally notify customers of these upcoming events so that customers can take actions to minimize the impact on the regular usage of the related circuits.

The challenge faced by many customers is that mostly every NSP defines its own maintenance notification format, even though in the
end the relevant information is mostly the same across NSPs. This library is built to parse notification formats from
several providers and to return always the same object struct that will make it easier to process them afterwards.

The format of this output is following the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) defined
during a NANOG meeting that aimed to promote the usage of the iCalendar format. Indeed, if the NSP is using the
proposed iCalendar format, the parser is straight-forward and there is no need to define custom logic, but this library
enables supporting other providers that are not using this proposed practice, getting the same outcome.

You can leverage on this library in your automation framework to process circuit maintenance notifications, and use the standarised output to handle your received circuit maintenance notifications in a simple way.

## How does it work?

Starting from a Provider parsing class, **multiple** parsers can be attached (in a specific order) and specific provider information (such as the default email used from the provider).

Each provider could use the standard ICal format commented above or define its custom HTML parsers, supporting multiple notification types for the same provider that could be transitioning from one type to another.

### Supported Providers

#### Supported providers using the BCOP standard

- EuNetworks
- NTT
- PacketFabric
- Telstra

#### Supported providers based on other parsers

- Cogent
- Lumen
- Megaport
- Telstra
- Zayo

> Note: Because these providers do not support the BCOP standard natively, maybe there are some gaps on the implemented parser that will be refined with new test cases. We encourage you to report related **issues**!

## Installation

The library is available as a Python package in pypi and can be installed with pip:
`pip install circuit-maintenance-parser`

## Usage

> Please, refer to the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) to understand the meaning
> of the output attributes.

## Python Library

```python
from circuit_maintenance_parser import init_parser

raw_text = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Maint Note//https://github.com/maint-notification//
BEGIN:VEVENT
SUMMARY:Maint Note Example
DTSTART;VALUE=DATE-TIME:20151010T080000Z
DTEND;VALUE=DATE-TIME:20151010T100000Z
DTSTAMP;VALUE=DATE-TIME:20151010T001000Z
UID:42
SEQUENCE:1
X-MAINTNOTE-PROVIDER:example.com
X-MAINTNOTE-ACCOUNT:137.035999173
X-MAINTNOTE-MAINTENANCE-ID:WorkOrder-31415
X-MAINTNOTE-IMPACT:OUTAGE
X-MAINTNOTE-OBJECT-ID;X-MAINTNOTE-OBJECT-IMPACT=NO-IMPACT:acme-widgets-as-a-service
X-MAINTNOTE-OBJECT-ID;X-MAINTNOTE-OBJECT-IMPACT=OUTAGE:acme-widgets-as-a-service-2
X-MAINTNOTE-STATUS:TENTATIVE
ORGANIZER;CN="Example NOC":mailto:noone@example.com
END:VEVENT
END:VCALENDAR
"""

data = {
  "raw": raw_text,
  "provider_type": "NTT"
}

parser = init_parser(**data)

parsed_notifications = parser.process()

print(parsed_notifications[0].to_json())
{
  "account": "137.035999173",
  "circuits": [
    {
      "circuit_id": "acme-widgets-as-a-service",
      "impact": "NO-IMPACT"
    },
    {
      "circuit_id": "acme-widgets-as-a-service-2",
      "impact": "OUTAGE"
    }
  ],
  "end": 1444471200,
  "maintenance_id": "WorkOrder-31415",
  "organizer": "mailto:noone@example.com",
  "provider": "example.com",
  "sequence": 1,
  "stamp": 1444435800,
  "start": 1444464000,
  "status": "TENTATIVE",
  "summary": "Maint Note Example",
  "uid": "42"
}
```

## CLI

```bash
$ circuit-maintenance-parser --raw-file tests/integration/data/ical/ical1
Circuit Maintenance Notification #0
{
  "account": "137.035999173",
  "circuits": [
    {
      "circuit_id": "acme-widgets-as-a-service",
      "impact": "NO-IMPACT"
    }
  ],
  "end": 1444471200,
  "maintenance_id": "WorkOrder-31415",
  "organizer": "mailto:noone@example.com",
  "provider": "example.com",
  "sequence": 1,
  "stamp": 1444435800,
  "start": 1444464000,
  "status": "TENTATIVE",
  "summary": "Maint Note Example",
  "uid": "42"
}
```

```bash
$ circuit-maintenance-parser --raw-file tests/integration/data/zayo/zayo1.html --parser zayo
Circuit Maintenance Notification #0
{
  "account": "clientX",
  "circuits": [
    {
      "circuit_id": "/OGYX/000000/ /ZYO /",
      "impact": "OUTAGE"
    }
  ],
  "end": 1601035200,
  "maintenance_id": "TTN-00000000",
  "organizer": "mr@zayo.com",
  "provider": "zayo",
  "sequence": 1,
  "stamp": 1599436800,
  "start": 1601017200,
  "status": "CONFIRMED",
  "summary": "Zayo will implement planned maintenance to troubleshoot and restore degraded span",
  "uid": "0"
}
```

# Contributing

Pull requests are welcomed and automatically built and tested against multiple versions of Python through Travis CI.

The project is following Network to Code software development guidelines and is leveraging:

- Black, Pylint, Mypy, Bandit and pydocstyle for Python linting and formatting.
- Unit and integration tests to ensure the library is working properly.

## Local Development

### Requirements

- Install `poetry`
- Install dependencies and library locally: `poetry install`
- Run CI tests locally: `invoke tests --local`

### How to add a new Circuit Maintenance provider?

1. If your Provider requires a custom parser, within `circuit_maintenance_parser/parsers`, **add your new parser**, inheriting from generic
   `Parser` class or custom ones such as `ICal` or `Html` and add a **unit test for the new provider parser**, with at least one test case under
   `tests/unit/data`.
2. Add new class in `providers.py` with the custom info, defining in `_parser_classes` the list of parsers that you will use, using the generic `ICal` and/or your custom parsers.
3. **Expose the new parser class** updating the map `SUPPORTED_PROVIDERS` in
   `circuit_maintenance_parser/__init__.py` to officially expose the parser.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)
