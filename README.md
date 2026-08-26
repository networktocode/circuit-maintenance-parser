# circuit-maintenance-parser

<p align="center">
  <a href="https://github.com/networktocode/circuit-maintenance-parser/actions"><img src="https://github.com/networktocode/circuit-maintenance-parser/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/"><img src="https://app.readthedocs.com/projects/circuit-maintenance-parser/badge/"></a>
  <a href="https://pypi.org/project/circuit-maintenance-parser/"><img src="https://img.shields.io/pypi/v/circuit-maintenance-parser"></a>
  <a href="https://pypi.org/project/circuit-maintenance-parser/"><img src="https://img.shields.io/pypi/dm/circuit-maintenance-parser"></a>
</p>

`circuit-maintenance-parser` is a Python library that parses circuit maintenance notifications from Network Service Providers (NSPs), converting heterogeneous formats to a well-defined structured format.

## Documentation

Full documentation for this library can be found over on the [Circuit-Maintenance-Parser Docs](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/) website:

- [User Guide](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/user/lib_overview/) - Overview, Using the Library, Getting Started.
- [Administrator Guide](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/admin/install/) - How to Install, Configure, Upgrade, or Uninstall the Library.
- [Developer Guide](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/dev/contributing/) - Extending the Library, Code Reference, Contribution Guide.
- [Release Notes / Changelog](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/admin/release_notes/).
- [Frequently Asked Questions](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/user/faq/).

## Context

Every network depends on external circuits provided by NSPs who interconnect them to the Internet, to office branches or to
external service providers such as Public Clouds.

Obviously, these services occasionally require operation windows to upgrade or to fix related issues, and usually, they happen in the form of **circuit maintenance periods**.
NSPs generally notify customers of these upcoming events so that customers can take actions to minimize the impact on the regular usage of the related circuits.

The challenge faced by many customers is that almost every NSP defines its own maintenance notification format, even though in the
end the relevant information is mostly the same across NSPs. This library is built to parse notification formats from
several providers and to return always the same object struct which will make it easier to process them afterwards.

The format of this output follows the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) defined
during a NANOG meeting that aimed to promote the usage of the iCalendar format. Indeed, if the NSP is using the
proposed iCalendar format, the parser is straightforward and there is no need to define custom logic, but this library
enables supporting other providers that are not using this proposed practice, getting the same outcome.

You can leverage this library in your automation framework to process circuit maintenance notifications and use the standardized [`Maintenance`](https://github.com/networktocode/circuit-maintenance-parser/blob/develop/circuit_maintenance_parser/output.py) model to handle your received circuit maintenance notifications in a simple way. Every `Maintenance` object contains the following attributes:

- **provider**: identifies the provider of the service that is the subject of the maintenance notification.
- **account**: identifies an account associated with the service that is the subject of the maintenance notification.
- **maintenance_id**: contains text that uniquely identifies (at least within the context of a specific provider) the maintenance that is the subject of the notification.
- **circuits**: list of circuits affected by the maintenance notification and their specific impact. Note that in a maintenance canceled or completed notification, some providers omit the circuit list, so this may be blank for maintenance notifications with a status of CANCELLED or COMPLETED.
- **start**: timestamp that defines the starting date/time of the maintenance in GMT.
- **end**: timestamp that defines the ending date/time of the maintenance in GMT.
- **stamp**: timestamp that defines the update date/time of the maintenance in GMT.
- **organizer**: defines the contact information included in the original notification.
- **status**: defines the overall status or confirmation for the maintenance.¹
- **summary**: human-readable details about this maintenance notification. May be an empty string.
- **sequence**: a sequence number for notifications involving this maintenance window. In practice, this is generally redundant with the **stamp** field and will be defaulted to `1` for most non-iCalendar parsed notifications.²
- **uid**: a unique (?) identifier for a thread of related notifications. In practice, this is generally redundant with the **maintenance_id** field and will be defaulted to `0` for most non-iCalendar parsed notifications.

> Please, refer to the [BCOP](https://github.com/jda/maintnote-std/blob/master/standard.md) to more details about the standardized meaning of these attributes.

¹ Per the BCOP, the **status** (`X-MAINTNOTE_STATUS`) is an optional field in iCalendar notifications. However, a `Maintenance` object will always contain a `status` value; in the case where an iCalendar notification omits this field, the `status` will be set to `"NO-CHANGE"`, and it's up to the consumer of this library to determine how to appropriately handle this case. Parsers of other notification formats are responsible for setting an appropriate value for this field based on the notification contents, and may or may not include `"NO-CHANGE"` as one of the possible reported values.

² Per the BCOP, the **sequence** is a mandatory field in iCalendar notifications. However, some NSPs have been seen to send notifications which, while otherwise consistent with the BCOP, omit the `SEQUENCE` field; in such cases, this library will report a sequence number of `-1`.

## Workflow

1. We instantiate a `Provider`, directly or via the `init_provider` method, that depending on the selected type will return the corresponding instance.
2. Get an instance of the `NotificationData` class. This instance groups together `DataParts` which each contain some content and a specific type (that will match a specific `Parser`). For example, a `NotificationData` might describe a received email message, with `DataParts` corresponding to the subject line and body of the email. There are factory methods to initialize a `NotificationData` describing a single chunk of binary data, as well as others to initialize one directly from a raw email message or `email.message.EmailMessage` instance.
3. Each `Provider` uses one or more `Processors` that will be used to build `Maintenances` when the `Provider.get_maintenances(data)` method is called.
4. Each `Processor` class uses one or more `Parsers` to process each type of data that it handles. It can have custom logic to combine the parsed data from multiple `Parsers` to create the final `Maintenance` object.
5. Each `Parser` class supports one or a set of related data types, and implements the `Parser.parse()` method used to retrieve a `Dict` with the relevant keys/values.

<p align="center">
<img src="https://raw.githubusercontent.com/networktocode/circuit-maintenance-parser/develop/docs/images/new_workflow.png" width="800" class="center">
</p>

By default, there is a `GenericProvider` that supports a `SimpleProcessor` using the standard `ICal` `Parser`, being the easiest path to start using the library in case the provider uses the reference iCalendar standard.

### Supported Providers

#### Supported providers using the BCOP standard

- Arelion (previously Telia)
- EuNetworks
- EXA (formerly GTT) (\*)
- NTT
- PacketFabric
- PCCW
- Telstra (\*)

#### Supported providers based on other parsers

- Apple
- ATT
- AWS
- AquaComms
- BSO
- Cogent
- Colt
- Crown Castle Fiber
- Equinix
- EXA (formerly GTT) (\*)
- HGC
- Global Cloud Xchange
- Google
- Hawaiki
- KPN
- Lumen
- Megaport
- Momentum
- Netflix (AS2906 only)
- PCCW
- Seaborn
- Sparkle
- Tata
- Telstra (\*)
- Turkcell
- Verizon
- Windstream
- Zayo

(\*) Providers in both lists, with BCOP standard and nonstandard parsers.

> Note: Because these providers do not support the BCOP standard natively, maybe there are some gaps on the implemented parser that will be refined with new test cases. We encourage you to report related **issues**!

#### LLM-powered Parsers

The library supports an optional parser option leveraging Large Language Models (LLM) to provide best-effort parsing when the specific parsers have not been successful.

> Warning: Some of these integrations, such as OpenAI, require of extras installations parameters. Check the [extras section](#extras)

When the appropriate environment variable(s) are set (see below), these LLM parsers are automatically appended after all existing processors for each defined Provider.

> These integrations may involve some costs for API usage. Use it carefully! As an order of magnitude, a parsing of an email with OpenAI GPT gpt-3.5-turbo model costs $0.004.

These are the currently supported LLM integrations:

- `PARSER_LLM_QUESTION_STR` (Optional), question to overwrite the default one. Change it carefully. It has precedence over `PARSER_LLM_QUESTION_FILEPATH`
- `PARSER_LLM_QUESTION_FILEPATH` (Optional), a path to a file that contains a question to overwrite the default one.

- [OpenAI](https://openai.com/product), these are the supported ENVs:
  - `PARSER_OPENAI_API_KEY` (Required): OpenAI API Key.
  - `PARSER_OPENAI_MODEL` (Optional): The LLM model to use, defaults to "gpt-3.5-turbo".

### Metadata

Each `Maintenance` comes with a `metadata` attribute to provide information about the provider used and the process and parsers used in the successful parsing of the maintenance.

This information is relevant to validate the actual content of the `Maintenance` because it may be generated using an LLM-powered parser which means that the confidence level is lower than using a pre-defined parser. You can check the `Metadata.generate_by_llm` boolean to check it.

## Installation

The library is available as a Python package in pypi and can be installed with pip:
`pip install circuit-maintenance-parser`

### Extras

#### OpenAI

`pip install circuit-maintenance-parser[openai]`

#### Xlsx Spreadsheets

Some providers may attach a spreadsheet in their circuit maintenance notifications. Support for this is provided by installing the optional xlsx package.

`pip install circuit-maintenance-parser[xlsx]`

## How to use it?

The library requires two things:

- The `notificationdata`: this is the data that the library will check to extract the maintenance notifications. It can be simple (only one data type and content, such as an iCalendar notification) or more complex (with multiple data parts of different types, such as from an email).
- The `provider` identifier: used to select the proper `Provider` which contains the `processor` logic to take the proper `Parsers` and use the data that they extract. By default, the `GenericProvider` (used when no other provider type is defined) will support parsing of `iCalendar` notifications using the recommended format.

### Python Library

The first step is to define the `Provider` that we will use to parse the notifications. As commented, there is a `GenericProvider` that implements the gold standard format and can be reused for any notification matching the expectations.

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

Notice that, either with the `GenericProvider` or `NTT` provider, we get the same result from the same data, because they are using exactly the same `Processor` and `Parser`. The only difference is that `NTT` notifications come without `organizer` and `provider` in the notification, and this info is fulfilled with some default values for the `Provider`, but in this case, the original notification contains all the necessary information, so the defaults are not used.

```python
ntt_maintenances = ntt_provider.get_maintenances(data_to_process)
assert maintenances_ntt == maintenances
```

Every maintenance contains the `metadata` attribute to understand how has been parsed:

```python
print(maintenances[0].metadata)
provider='genericprovider' processor="SimpleProcessor" parsers=["ICal"], generated_by_llm=False
```

### CLI

There is also a `cli` entry point `circuit-maintenance-parser` which offers easy access to the library using a few arguments:

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

## Contributing

Pull requests are welcomed and automatically built and tested through GitHub Actions.

The project is following Network to Code software development guidelines and is leveraging:

- Ruff for Python linting and formatting.
- Pylint for additional static analysis.
- Unit and integration tests to ensure the library is working properly.

For more details, see the [Contributing Guide](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/dev/contributing/) and [Development Environment Guide](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/dev/dev_environment/).

## Questions

For any questions or comments, please check the [FAQ](https://docs.networktocode.com/projects/circuit-maintenance-parser/en/latest/user/faq/) first. Feel free to also swing by the [Network to Code Slack](https://networktocode.slack.com/) (channel `#networktocode`), sign up [here](http://slack.networktocode.com/) if you don't have an account.

## License notes

This library uses a Basic World Cities Database by Pareto Software, LLC, the owner of Simplemaps.com: The Provider offers a Basic World Cities Database free of charge. This database is licensed under the Creative Commons Attribution 4.0 license as described at: https://creativecommons.org/licenses/by/4.0/.
