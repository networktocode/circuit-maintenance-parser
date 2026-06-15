# Using the Library

This document describes common use-cases and scenarios for this library.

## General Usage

The library follows a three-step pattern:

1. **Initialize a Provider** - Select the appropriate provider for your NSP.
2. **Create NotificationData** - Wrap your notification content (iCal, HTML, email, etc.).
3. **Parse Maintenances** - Call `provider.get_maintenances(data)` to get structured results.

## Use-cases and common workflows

### Parsing Email Notifications

Many providers send maintenance notifications via email. You can parse an entire email message:

```python
from circuit_maintenance_parser import init_provider, NotificationData

provider = init_provider("zayo")

with open("maintenance_email.eml", "rb") as f:
    raw_email = f.read()

data = NotificationData.init_from_emailmessage(raw_email)
maintenances = provider.get_maintenances(data)
```

### Parsing HTML Notifications

For providers that send HTML-formatted notifications:

```python
from circuit_maintenance_parser import init_provider, NotificationData

provider = init_provider("lumen")

with open("notification.html", "rb") as f:
    html_content = f.read()

data = NotificationData.init_from_raw("html", html_content)
maintenances = provider.get_maintenances(data)
```

### Using LLM-powered Parsing

When specific parsers are insufficient, LLM-powered parsing can provide best-effort results. Set the required environment variables:

```bash
export PARSER_OPENAI_API_KEY="your-api-key"
```

Install the OpenAI extra:

```bash
pip install circuit-maintenance-parser[openai]
```

The LLM parsers are automatically appended after all existing processors. You can check the `metadata` attribute to see if LLM was used:

```python
for maintenance in maintenances:
    if maintenance.metadata.generated_by_llm:
        print("Warning: This maintenance was parsed by LLM")
```

### Checking Parse Metadata

Every maintenance includes metadata about how it was parsed:

```python
maintenance = maintenances[0]
print(maintenance.metadata)
# provider='genericprovider' processor="SimpleProcessor" parsers=["ICal"], generated_by_llm=False
```

## Supported Providers

For a complete list of supported providers, see the [README](https://github.com/networktocode/circuit-maintenance-parser#supported-providers).
