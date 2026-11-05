"""Comcast parser."""

import re
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

# Comcast labels times with the standard-time abbreviation all year round (e.g. "EST" in October),
# so the abbreviations are mapped to their region to let daylight saving be applied.
TIMEZONE_MAP = {
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "UTC": "Etc/UTC",
    "GMT": "Etc/UTC",
}

TIME_PATTERN = r"(\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M)\s+([A-Z]{2,4})"

WINDOW_RE = re.compile(
    rf"on\s+(\d{{4}}-\d{{2}}-\d{{2}})\s+between\s+{TIME_PATTERN}\s+and\s+conclude\s+on\s+"
    rf"(\d{{4}}-\d{{2}}-\d{{2}})\s+at\s+{TIME_PATTERN}",
    re.IGNORECASE,
)
# The activity sentence ends at the first period followed by whitespace, so dots inside hostnames or versions are kept.
SUMMARY_RE = re.compile(r"maintenance activity:\s*(.+?)\s*\.(?:\s|$)", re.IGNORECASE)
ATTENTION_RE = re.compile(r"Attention:")
RESCHEDULED_RE = re.compile(r"has been rescheduled", re.IGNORECASE)
DEFAULT_ACCOUNT = "Customer info unavailable"
TICKET_RE = re.compile(r"reference ticket\s+#?\s*([A-Z]+\d+)")
CIRCUIT_HEADER_RE = re.compile(r"^\s*Circuit ID\s*$", re.IGNORECASE)
CIRCUIT_PREFIX_RE = re.compile(r"^cid:\s*", re.IGNORECASE)


class HtmlParserComcast1(Html):
    """Notifications Parser for Comcast Business HTML notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse a Comcast Business maintenance notification."""
        # The relevant values are split across <strong> tags, so work on the whole body text instead.
        text = " ".join(soup.get_text(" ").split())
        data: Dict = {"status": Status.RE_SCHEDULED if RESCHEDULED_RE.search(text) else Status.CONFIRMED}

        window = WINDOW_RE.search(text)
        if window:
            data["start"] = self._parse_datetime(window.group(1), window.group(2), window.group(3))
            data["end"] = self._parse_datetime(window.group(4), window.group(5), window.group(6))

        summary = SUMMARY_RE.search(text)
        if summary:
            data["summary"] = summary.group(1).strip(" #")

        # The account name is the first <strong> after the "Attention:" label.
        attention = soup.find(string=ATTENTION_RE)
        account = attention.find_next("strong") if attention else None
        data["account"] = (account.get_text(" ", strip=True) if account else "") or DEFAULT_ACCOUNT

        ticket = TICKET_RE.search(text)
        if ticket:
            data["maintenance_id"] = ticket.group(1)

        data["circuits"] = [
            CircuitImpact(circuit_id=circuit_id, impact=Impact.OUTAGE)
            for circuit_id in dict.fromkeys(self._get_circuit_ids(soup))
        ]

        return [data]

    @staticmethod
    def _get_circuit_ids(soup: ResultSet) -> List[str]:
        """Return the values listed under the "Circuit ID" table header, with or without the "cid:" prefix."""
        circuit_ids = []
        for header in soup.find_all(string=CIRCUIT_HEADER_RE):
            header_cell = header.find_parent(["td", "th"])
            header_row = header_cell.find_parent("tr")
            column = header_row.find_all(["td", "th"], recursive=False).index(header_cell)
            for row in header_row.find_next_siblings("tr"):
                cells = row.find_all(["td", "th"], recursive=False)
                if len(cells) <= column:
                    continue
                circuit_id = CIRCUIT_PREFIX_RE.sub("", cells[column].get_text(" ", strip=True))
                if circuit_id:
                    circuit_ids.append(circuit_id)
        return circuit_ids

    @staticmethod
    def _parse_datetime(date_str: str, time_str: str, tz_abbr: str) -> int:
        """Convert Comcast date, time and timezone strings into a UTC timestamp."""
        time_str = time_str.replace(" ", "").upper()
        time_format = "%I:%M:%S%p" if time_str.count(":") == 2 else "%I:%M%p"
        dt_obj = datetime.strptime(f"{date_str} {time_str}", f"%Y-%m-%d {time_format}")

        tz_name = TIMEZONE_MAP.get(tz_abbr.upper())
        if tz_name is None:
            raise ValueError(f"Unknown timezone: {tz_abbr}")

        return int(dt_obj.replace(tzinfo=ZoneInfo(tz_name)).timestamp())
