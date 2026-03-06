# Extending the Library

Extending the library is welcome, however it is best to open an issue first, to ensure that a PR would be accepted and makes sense in terms of features and design.

## Adding a New Provider

Adding a new `Provider` is straightforward. Here's an example adding support for an imaginary provider, ABCDE, that uses HTML notifications.

### Step 1: Create the Parser

Create a new file `circuit_maintenance_parser/parsers/abcde.py` with your custom parser(s):

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

### Step 2: Create the Provider

Define a new class in `circuit_maintenance_parser/provider.py`:

```python
class ABCDE(GenericProvider):
    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserABCDE1]),
    ]
    _default_organizer = "noc@abcde.com"
```

The `_processors` attribute is a list of `Processor` instances that use several data `Parsers`. The `_default_organizer` fills the `organizer` attribute if missing from the notification.

### Step 3: Expose the Provider

Update `circuit_maintenance_parser/__init__.py`:

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

### Step 4: Add Tests

- Add parser tests in `tests/unit/test_parsers.py`
- Add provider/end-to-end tests in `tests/unit/test_e2e.py`
- Add sample data in `tests/unit/data/abcde/`

You can anonymize IPv4 and IPv6 addresses in test data using `invoke anonymize-ips`.
