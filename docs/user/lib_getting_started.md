# Getting Started with the Library

This document provides a step-by-step tutorial on how to get the library going and how to use it.

## Install the Library

To install the library, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First steps with the Library

### Parse an iCalendar Notification

The simplest use case is parsing a standard iCalendar (BCOP) notification:

```python
from circuit_maintenance_parser import init_provider, NotificationData

# Initialize a generic provider (supports standard iCalendar format)
provider = init_provider()

# Create notification data from raw iCalendar content
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
X-MAINTNOTE-OBJECT-ID;X-MAINTNOTE-OBJECT-IMPACT=OUTAGE:circuit-1
X-MAINTNOTE-STATUS:TENTATIVE
ORGANIZER;CN="Example NOC":mailto:noone@example.com
END:VEVENT
END:VCALENDAR
"""

data = NotificationData.init_from_raw("ical", raw_data)
maintenances = provider.get_maintenances(data)

print(maintenances[0].to_json())
```

### Parse a Provider-Specific Notification

For providers that don't use the standard iCalendar format, initialize a provider-specific instance:

```python
from circuit_maintenance_parser import init_provider

# Initialize a provider-specific parser (e.g., Zayo)
zayo_provider = init_provider("zayo")
```

### Use the CLI

The library also provides a command-line interface:

```bash
circuit-maintenance-parser --data-file notification.eml --data-type email --provider-type zayo
```

## What are the next steps?

You can check out the [Use Cases](./lib_use_cases.md) section for more examples.
