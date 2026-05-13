"""SummitIG Parser."""

import re
from datetime import datetime
from typing import Any, ClassVar, Dict, List
from zoneinfo import ZoneInfo

from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status


class HtmlParserSummitIG(Html):
    """Custom parser for SummitIG HTML circuit maintenance notifications."""

    STATUS_MAP: ClassVar[Dict[str, Status]] = {
        "Scheduled": Status.CONFIRMED,
        "Restored": Status.COMPLETED,
        "Splicing": Status.IN_PROCESS,
    }

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse a summit circuit maintenance email.

        Args:
            soup (ResultSet): beautiful soup object containing the html portion of an email.

        Returns:
            List[Dict]: Data dictionaries containing the circuit maintenance data.
        """
        data: Dict[str, Any] = {}

        table = soup.find("table")
        if table is None:
            return [data]

        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            key = th.get_text(strip=True)
            value = td.get_text(strip=True)
            self._apply_field(data, key, value)

        return [data]

    def _apply_field(self, data: Dict[str, Any], key: str, value: str) -> None:
        """Map a table field into the parsed data dictionary.

        Args:
            data (dict[str, Any]): a dictionary containing tags and their values.
            key (str): the key that we want to map to the appropriate field.
            value (str): the value that we want to associate with the appropriate field.
        """
        simple_fields = {
            "Company": ("account", value),
            "Event": ("maintenance_id", value),
            "Description": ("summary", value),
        }

        if key in simple_fields:
            field_name, field_value = simple_fields[key]
            data[field_name] = field_value
            return

        if key == "Status":
            data["status"] = self.STATUS_MAP.get(value, Status.TENTATIVE)
            return

        if key == "Circuits":
            circuits = []
            for circuit in value.split(","):
                c = CircuitImpact(circuit_id=circuit, impact=Impact.OUTAGE)
                circuits.append(c)
            data["circuits"] = circuits
            return

        if "Start" in key:
            timezone = _extract_timezone(key)
            full_time = _parse_summit_datetime(value, timezone)
            data["start"] = full_time
            return

        if "End" in key:
            timezone = _extract_timezone(key)
            full_time = _parse_summit_datetime(value, timezone)
            data["end"] = full_time


def _extract_timezone(key: str) -> str:
    """Extract a timezone from a SummitIG table start or end time.

    Args:
        key (str): A string in the format of 'Start Time (EST)' or 'End Time (EST)'.

    Returns:
        str: The timezone (EST, CDT, ...) extracted from the input.
    """
    # We need to pull the timezone out of the key
    # Start Time (EST)
    match = re.search(r"\((.*?)\)", key)
    if not match:
        raise ValueError(f"No timezone found in Key: '{key}'")
    return match.group(1)


def _parse_summit_datetime(date_time: str, timezone: str) -> int:
    """Create a unix timestamp based on a date and a timezone provided by Summit.

    Args:
        date_time: A datetime string without the timezone '2/21/2025'.
        timezone: The abbreviated timezone 'EST', 'PST', etc.

    Returns:
        int: The unix timestamp based on the datetime and timezone inputs.
    """
    # Parse datetime string
    dt = datetime.strptime(date_time, "%m/%d/%Y %I:%M %p")

    # Map timezone abbreviation → IANA timezone
    tz_map = {
        "EST": "America/New_York",
        "EDT": "America/New_York",
        "CST": "America/Chicago",
        "CDT": "America/Chicago",
        "MST": "America/Denver",
        "MDT": "America/Denver",
        "PST": "America/Los_Angeles",
        "PDT": "America/Los_Angeles",
    }

    if timezone not in tz_map:
        raise ValueError(f"Unknown timezone: {timezone}")

    # Attach timezone
    dt = dt.replace(tzinfo=ZoneInfo(tz_map[timezone]))

    return int(dt.timestamp())
