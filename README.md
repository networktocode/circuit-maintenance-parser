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

You can leverage this library in your automation framework to process circuit maintenance notifications, and use the standardized [`Maintenance`](https://github.com/networktocode/circuit-maintenance-parser/blob/develop/circuit_maintenance_parser/output.py) model to handle your received circuit maintenance notifications in a simple way. Every `Maintenance` object contains the following attributes:

- **provider**: identifies the provider of the service that is the subject of the maintenance notification.
- **account**: identifies an account associated with the service that is the subject of the maintenance notification.
- **maintenance_id**: contains text that uniquely identifies (at least within the context of a specific provider) the maintenance that is the subject of the notification.
- **circuits**: list of circuits affected by the maintenance notification and their specific impact.
- **start**: timestamp that defines the starting date/time of the maintenance in GMT.
- **end**: timestamp that defines the ending date/time of the maintenance in GMT.
- **stamp**: timestamp that defines the update date/time of the maintenance in GMT.
- **organizer**: defines the contact information included in the original notification.
- **status**: defines the overall status or confirmation for the maintenance.¹
- **summary**: human-readable details about this maintenance notification. May be an empty string.
- **sequence**: a sequence number for notifications involving this maintenance window. In practice this is generally redundant with the **stamp** field, and will be defaulted to `1` for most non-iCalendar parsed notifications.²
- **uid**: a unique (?) identifer for a thread of related notifications. In practice this is generally redundant with the **maintenance_id** field, and will be defaulted to `0` for most non-iCalendar parsed notifications.

> Please, refer to the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) to more details about the standardized meaning of these attributes.

¹ Per the BCOP, **status** (`X-MAINTNOTE_STATUS`) is an optional field in iCalendar notifications. However, a `Maintenance` object will always contain a `status` value; in the case where an iCalendar notification omits this field, the `status` will be set to `"NO-CHANGE"`, and it's up to the consumer of this library to determine how to appropriately handle this case. Parsers of other notification formats are responsible for setting an appropriate value for this field based on the notification contents, and may or may not include `"NO-CHANGE"` as one of the possible reported values.

² Per the BCOP, **sequence** is a mandatory field in iCalendar notifications. However, some NSPs have been seen to send notifications which, while otherwise consistent with the BCOP, omit the `SEQUENCE` field; in such cases, this library will report a sequence number of `-1`.

## Workflow

1. We instantiate a `Provider`, directly or via the `init_provider` method, that depending on the selected type will return the corresponding instance.
2. Get an instance of the `NotificationData` class. This instance groups together `DataParts` which each contain some content and a specific type (that will match a specific `Parser`). For example, a `NotificationData` might describe a received email message, with `DataParts` corresponding to the subject line and body of the email. There are factory methods to initialize a `NotificationData` describing a single chunk of binary data, as well as others to initialize one directly from a raw email message or `email.message.EmailMessage` instance.
3. Each `Provider` uses one or more `Processors` that will be used to build `Maintenances` when the `Provider.get_maintenances(data)` method is called.
4. Each `Processor` class uses one or more `Parsers` to process each type of data that it handles. It can have custom logic to combine the parsed data from multiple `Parsers` to create the final `Maintenance` object.
5. Each `Parser` class supports one or a set of related data types, and implements the `Parser.parse()` method used to retrieve a `Dict` with the relevant keys/values.

<p align="center">
<img src="https://raw.githubusercontent.com/networktocode/circuit-maintenance-parser/develop/docs/images/new_workflow.png" width="800" class="center">
</p>

By default, there is a `GenericProvider` that support a `SimpleProcessor` using the standard `ICal` `Parser`, being the easiest path to start using the library in case the provider uses the reference iCalendar standard.

### Supported Providers

#### Supported providers using the BCOP standard

- Arelion (previously Telia)
- EuNetworks
- NTT
- PacketFabric
- Telstra

#### Supported providers based on other parsers

- AWS
- AquaComms
- BSO
- Cogent
- Colt
- Equinix
- EXA (formerly GTT)
- HGC
- Lumen
- Megaport
- Momentum
- Seaborn
- Sparkle
- Telstra
- Turkcell
- Verizon
- Zayo

> Note: Because these providers do not support the BCOP standard natively, maybe there are some gaps on the implemented parser that will be refined with new test cases. We encourage you to report related **issues**!

## Installation

The library is available as a Python package in pypi and can be installed with pip:
`pip install circuit-maintenance-parser`

## How to use it?

The library requires two things:

- The `notificationdata`: this is the data that the library will check to extract the maintenance notifications. It can be simple (only one data type and content, such as an iCalendar notification) or more complex (with multiple data parts of different types, such as from an email).
- The `provider` identifier: used to select the proper `Provider` which contains the `processor` logic to take the proper `Parsers` and use the data that they extract. By default, the `GenericProvider` (used when no other provider type is defined) will support parsing of `iCalendar` notifications using the recommended format.

### Python Library

First step is to define the `Provider` that we will use to parse the notifications. As commented, there is a `GenericProvider` that implements the gold standard format and can be reused for any notification matching the expectations.

```python
from circuit_maintenance_parser import init_provider

generic_provider = init_provider()

type(generic_provider)
<class 'circuit_maintenance_parser.provider.GenericProvider'>
```

However, usually some `Providers` don't fully implement the standard and maybe some information is missing, for example the `organizer` email or maybe a custom logic to combine information is required, so we allow custom `Providers`:

```python
ntt_provider = init_provider("ntt")

type(ntt_provider)
<class 'circuit_maintenance_parser.provider.NTT'>
```

Once we have the `Provider` ready, we need to initialize the data to process, we call it `NotificationData` and can be initialized from a simple content and type or from more complex structures, such as an email.

```python
from circuit_maintenance_parser import NotificationData

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

data_to_process = NotificationData.init_from_raw("ical", raw_data)

type(data_to_process)
<class 'circuit_maintenance_parser.data.NotificationData'>
```

Finally, with we retrieve the maintenances (it is a `List` because a notification can contain multiple maintenances) from the data calling the `get_maintenances` method from the `Provider` instance:

```python
maintenances = generic_provider.get_maintenances(data_to_process)

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

Notice that, either with the `GenericProvider` or `NTT` provider, we get the same result from the same data, because they are using exactly the same `Processor` and `Parser`. The only difference is that `NTT` notifications come without `organizer` and `provider` in the notification, and this info is fulfilled with some default values for the `Provider`, but in this case the original notification contains all the necessary information, so the defaults are not used.

```python
ntt_maintenances = ntt_provider.get_maintenances(data_to_process)
assert maintenances_ntt == maintenances
```

### CLI

There is also a `cli` entrypoint `circuit-maintenance-parser` which offers easy access to the library using few arguments:

- `data-file`: file storing the notification.
- `data-type`: `ical`, `html` or `email`, depending on the data type.
- `provider-type`: to choose the right `Provider`. If empty, the `GenericProvider` is used.

```bash
circuit-maintenance-parser --data-file "/tmp/___ZAYO TTN-00000000 Planned MAINTENANCE NOTIFICATION___.eml" --data-type email --provider-type zayo
Circuit Maintenance Notification #0
{
  "account": "some account",
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

## How to Extend the Library?

Even though the library aims to include support for as many providers as possible, it's likely that not all the thousands of NSP are supported and you may need to add support for some new one. Adding a new `Provider` is quite straightforward, and in the following example we are adding support for an imaginary provider, ABCDE, that uses HTML notifications.

First step is creating a new file: `circuit_maintenance_parser/parsers/abcde.py`. This file will contain all the custom parsers needed for the provider and it will import the base classes for each parser type from `circuit_maintenance_parser.parser`. In the example, we only need to import `Html` and in the child class implement the methods required by the class, in this case `parse_html()` which will return a `dict` with all the data that this `Parser` can extract. In this case we have to helper methods, `_parse_bs` and `_parse_tables` that implement the logic to navigate the notification data.

```python
from typing import Dict
import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore
from circuit_maintenance_parser.parser import Html

class HtmlParserABCDE1(Html):
    def parse_html(self, soup: ResultSet) -> Dict:
        data = {}
        self._parse_bs(soup.find_all("b"), data)
        self._parse_tables(soup.find_all("table"), data)
        return [data]

    def _parse_bs(self, btags: ResultSet, data: Dict):
      ...

    def _parse_tables(self, tables: ResultSet, data: Dict):
      ...
```

Next step is to create the new `Provider` by defining a new class in `circuit_maintenance_parser/provider.py`. This class that inherits from `GenericProvider` only needs to define two attributes:

- `_processors`: is a `list` of `Processor` instances that uses several data `Parsers`. In this example, we don't need to create a new custom `Processor` because the combined logic serves well (the most likely case), and we only need to use the new defined `HtmlParserABCDE1` and also the generic `EmailDateParser` that extract the email date. Also notice that you could have multiple `Processors` with different `Parsers` in this list, supporting several formats.
- `_default_organizer`: this is a default helper to fill the `organizer` attribute in the `Maintenance` if the information is not part of the original notification.

```python
class ABCDE(GenericProvider):
    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserABCDE1]),
    ]
    _default_organizer = "noc@abcde.com"
```

And expose the new `Provider` in `circuit_maintenance_parser/__init__.py`:

```python
from .provider import (
    GenericProvider,
    ABCDE,
    ...
)

SUPPORTED_PROVIDERS = (
    GenericProvider,
    ABCDE,
    ...
)
```

Last, but not least, you should update the tests!

- Test the new `Parser` in `tests/unit/test_parsers.py`
- Test the new `Provider` logic in `tests/unit/test_e2e.py`

... adding the necessary data samples in `tests/unit/data/abcde/`.

> You can anonymize your IPv4 and IPv6 addresses using the `invoke anonymize-ips --local`. Keep in mind that only IPv4 addresses for documentation purposes (RFC5737: "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24") are preserved, in case you need to check these IPs in your test output (unlikely)

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
   - The `Provider` also supports the definition of a `_include_filter` and a `_exclude_filter` to limit the notifications that are actually processed, avoiding false positive errors for notification that are not relevant.
4. Update the `unit/test_e2e.py` with the new provider, providing some data to test and validate the final `Maintenances` created.
5. **Expose the new `Provider` class** updating the map `SUPPORTED_PROVIDERS` in `circuit_maintenance_parser/__init__.py` to officially expose the `Provider`.

## Questions

For any questions or comments, please check the [FAQ](FAQ.md) first and feel free to swing by the [Network to Code slack channel](https://networktocode.slack.com/) (channel #networktocode).
Sign up [here](http://slack.networktocode.com/)

## License notes

This library uses a Basic World Cities Database by Pareto Software, LLC, the owner of Simplemaps.com: The Provider offers a Basic World Cities Database free of charge. This database is licensed under the Creative Commons Attribution 4.0 license as described at: https://creativecommons.org/licenses/by/4.0/.
