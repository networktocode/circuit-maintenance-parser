# circuit-maintenance-parser

`circuit-maintenance-parser` is a Python library that parses NSP(Network Service Provider)'s maintenance notifications, converting heterogenuous formats to a well-defined structured format.

## Context

Every network depends on external circuits provided by NSPs who interconnect them to Internet, to office branches or to
external service providers such as Public Clouds.

Obviously, these services require from operation windows to upgrade or to fix related issues, and usually they come in
format of **circuit maintenances** that should be notified back to the customers via notifications to take actions to minimize the impact on the regular usage of the related circuits.

The challenge myriad of customers are facing is that mostly every NSP defines its own maintenance format, even in the
end the relevant information is mostly the same across them. This library is built to parse notification formats from
several providers and to return always the same object struct that will make easier to process them afterwards.

The format of this output is following the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) defined
during a NANOG meeting that aimed to promote the usage of the iCalendar format. Indeed, if the NSP is using the
proposed iCalendar format, the parser is straight-forward and no need to defined a custom logic, but this library
enables supporting other providers that are not using this proposed practice, getting the same outcome.

You can leverage on this library in your automation framework to process circuit maintenance notifications, and use the standarised output to handle your received circuit maintenances in a simple way.

## Installation

### Using Pip

The library is available as a Python package in pypi and can be installed with pip:
`pip install circuit-maintenance-parser`

### Using Poetry

The library can be installed with `poetry`: `poetry install`

## Usage

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
  "subject": "this is a circuit maintenance from some NSP",
  "sender": "support@networkserviceprovider.com",
  "source": "gmail",
  "raw": raw_text,
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

> Please, refer to the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) to understand the meaning
> of the output attributes.

# Contributing

Pull requests are welcomed and automatically built and tested against multiple version of Python through TravisCI.

The project is following Network to Code software development guideline and is leveraging:

- Black, Pylint, Mypy, Bandit and pydocstyle for Python linting and formatting.
- Unit and integration test to ensure the library is working properly.

## Local Development

### Requirements

- Install `poetry`
- Install dependencies and library locally: `poetry install`
- Run CI tests locally: `invoke tests --local`

### How to add a new Circuit Maintenance parser?

1. Within `circuit_maintenance_parser/parsers`, **add your new parser**, inheriting from generic
   `MaintenanceNotification` class or custom ones such as `ICal` or `Html`.
2. Add a Circuit Maintenance **integration test for the new provider parser**, with at least one test case under
   `tests/integration/data`.
3. **Expose the new parser class** updating the map `SUPPORTED_PROVIDER_PARSERS` in
   `circuit_maintenance_parser/__init__.py` to officially expose the parser.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)
