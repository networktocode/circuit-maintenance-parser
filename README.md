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

## Workflow

1. We instantiate a `Provider`, directly or via the `init_provider` method, that depending on the selected type will return the corresponding instance.
2. Each `Provider` have already defined multiple `Processors` that will be used to get the `Maintenances` when the `Provider.get_maintenances(data)` method is called.
3. Each `Processor` class can have a pre defined logic to combine the data extracted from the notifications and create the final `Maintenance` object, and receives a `List` of multiple `Parsers` that will be to `parse` each type of data.
4. Each `Parser` class supports one or more data types and implements the `Parser.parse()` method used to retrieve a `Dict` with the relevant key/values.
5. When calling the `Provider.get_maintenances(data)`, the `data` argument is an instance of `NotificationData` (which is just a collection of multiple `DataParts`, each one with a `type` and a `content`) that will be used by the corresponding `Parser` when the `Processor` will try to match them.

By default, there is a `GenericProvider` that support a `SimpleProcessor` using the standard `ICal` `Parser`, being the easiest path to start using the library in case the provider uses the reference iCalendar standard.

### Supported Providers

#### Supported providers using the BCOP standard

- EuNetworks
- NTT
- PacketFabric
- Telia
- Telstra

#### Supported providers based on other parsers

- AquaComms
- Cogent
- Colt
- GTT
- HGC
- Lumen
- Megaport
- Momentum
- Seaborn
- Telstra
- Turkcell
- Verizon
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
from circuit_maintenance_parser import init_provider, init_data_raw

raw_data = b"""BEGIN:VCALENDAR
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

ntt_provider = init_provider("ntt")

data_to_process = init_data_raw("ical", raw_data)

maintenances = ntt_provider.get_maintenances(data_to_process)

print(maintenances[0].to_json())
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
$ circuit-maintenance-parser --data-file tests/unit/data/ical/ical1 --data-type ical
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
$ circuit-maintenance-parser --data-file tests/unit/data/zayo/zayo1.html --data-type html --provider-type zayo
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

```bash
circuit-maintenance-parser --data-file "/tmp/___ZAYO TTN-00000000 Planned MAINTENANCE NOTIFICATION___.eml" --data-type email --provider-type zayo
Circuit Maintenance Notification #0
{
  "account": "Linode",
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

1. Define the `Parsers`(inheriting from some of the generic `Parsers` or a new one) that will extract the data from the notification, that could contain itself multiple `DataParts`. The `data_type` of the `Parser` and the `DataPart` have to match. The custom `Parsers` will be placed in the `parsers` folder.
2. Update the `unit/test_parsers.py` with the new parsers, providing some data to test and validate the extracted data.
3. Define a new `Provider` inheriting from the `GenericProvider`, defining the `Processors` and the respective `Parsers` to be used. Maybe you can reuse some of the generic `Processors` or maybe you will need to create a custom one. If this is the case, place it in the `processors` folder.
4. Update the `unit/test_e2e.py` with the new provider, providing some data to test and validate the final `Maintenances` created.
5. **Expose the new `Provider` class** updating the map `SUPPORTED_PROVIDERS` in `circuit_maintenance_parser/__init__.py` to officially expose the `Provider`.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)
