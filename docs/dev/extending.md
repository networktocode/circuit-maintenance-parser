# Extending the Library

Extending the library is welcome, however it is best to open an issue first, to ensure that a PR would be accepted and makes sense in terms of features and design.

## Adding a New Provider

Adding a new `Provider` is straightforward. Here's an example adding support for an imaginary provider, ABCDE, that uses HTML notifications.

### Step 1: Create the Parser

Create a new file `circuit_maintenance_parser/parsers/abcde.py` with your custom parser(s). This file will contain all the custom parsers needed for the provider and will import the base classes for each parser type from `circuit_maintenance_parser.parser`:

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

### Step 2: Update Parser Tests

Update `tests/unit/test_parsers.py` with the new parsers, providing some data to test and validate the extracted data.

### Step 3: Create the Provider

Define a new `Provider` by creating a new class in `circuit_maintenance_parser/provider.py`. This class inherits from `GenericProvider` and only needs to define two attributes:

- `_processors`: a list of `Processor` instances that use several data `Parsers`. You can reuse generic `Processors` or create custom ones. If creating a custom one, place it in the `processors` folder.
    - The `Provider` also supports the definition of a `_include_filter` and a `_exclude_filter` to limit the notifications that are actually processed, avoiding false positive errors for notifications that are not relevant.
- `_default_organizer`: a default helper to fill the `organizer` attribute in the `Maintenance` if the information is not part of the original notification.

```python
class ABCDE(GenericProvider):
    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserABCDE1]),
    ]
    _default_organizer = "noc@abcde.com"
```

### Step 4: Update End-to-End Tests

Update `tests/unit/test_e2e.py` with the new provider, providing some data to test and validate the final `Maintenances` created.

### Step 5: Expose the Provider

Update the map `SUPPORTED_PROVIDERS` in `circuit_maintenance_parser/__init__.py` to officially expose the `Provider`:

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

### Step 6: Run Unit Tests

You can run some tests to verify that your new unit tests do not cause issues with existing tests, and in general they work as expected. You can do this by running `pytest --log-cli-level=DEBUG --capture=tee-sys`. You can narrow down the tests that you want to execute with the `-k` flag. If successful, your results should look similar to the following:

```
-> % pytest --log-cli-level=DEBUG --capture=tee-sys -k test_parsers
...omitted debug logs...
====================================================== 99 passed, 174 deselected, 17 warnings in 10.35s ======================================================
```

### Step 7: Run CI Tests Locally

Run some final CI tests locally to ensure that there is no linting/formatting issues with your changes. You should look to get a code score of 10/10. See the example below: `invoke tests`

```
-> % poetry run invoke tests
DOCKER - Running command: ruff format --check . container: circuit_maintenance_parser:latest
52 files already formatted
DOCKER - Running command: ruff check --output-format concise . container: circuit_maintenance_parser:latest
All checks passed!
DOCKER - Running command: find . -name "*.py" | grep -vE "tests/unit" | xargs pylint container: circuit_maintenance_parser:latest

------------------------------------
Your code has been rated at 10.00/10
```

### Test Data

Add the necessary data samples in `tests/unit/data/abcde/`.

You can anonymize your IPv4 and IPv6 addresses using `invoke anonymize-ips`. Keep in mind that only IPv4 addresses for documentation purposes (RFC5737: "192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24") are preserved, in case you need to check these IPs in your test output (unlikely).

## Debugging the Library Locally

1. `poetry install` updates the library and its dependencies locally.
2. `circuit-maintenance-parser` is now built with your recent local changes.

If you were to add loggers or debuggers to one of the classes:

```python
class HtmlParserZayo1(Html):
    def parse_bs(self, btags: ResultSet, data: dict):
        """Parse B tag."""
        raise Exception('Debugging exception')
```

After running `poetry install`:

```
-> % circuit-maintenance-parser --data-file ~/Downloads/zayo.eml --data-type email --provider-type zayo
Provider processing failed: Failed creating Maintenance notification for Zayo.
Details:
- Processor CombinedProcessor from Zayo failed due to: Debugging exception
```

> Note: `invoke build` will result in an error due to no Dockerfile. This is expected as the library runs simple pytest testing without a container.

```
-> % invoke build
Building image circuit-maintenance-parser:2.2.2-py3.8
#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 2B done
#1 DONE 0.0s
WARNING: failed to get git remote url: fatal: No remote configured to list refs from.
ERROR: failed to solve: rpc error: code = Unknown desc = failed to solve with frontend dockerfile.v0: failed to read dockerfile: open /var/lib/docker/tmp/buildkit-mount1243547759/Dockerfile: no such file or directory
```
