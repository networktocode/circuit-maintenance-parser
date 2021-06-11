"""Cogent parser."""
import logging
import re
from typing import Dict

from datetime import datetime
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status


logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class ParserCogent(Html):
    """Notifications Parser for Cogent notifications."""

    provider_type: str = "cogent"

    # Default values for cogent notifications
    _default_provider = "cogent"
    _default_organizer = "support@cogentco.com"

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_div(soup.find_all("div", class_="a3s aiL"), data)
            self.parse_title(soup.find_all("title"), data)
            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_div(self, divs: ResultSet, data: Dict):
        """Parse <div> tag."""
        for div in divs:
            for line in div.text.splitlines():
                if line.endswith("Network Maintenance"):
                    data["summary"] = line
                elif line.startswith("Dear"):
                    match = re.search("Dear (.*),", line)
                    if match:
                        data["account"] = match.group(1)
                elif line.startswith("Start time:"):
                    match = re.search("Start time: (.*) \(local time\) (\d+/\d+/\d+)", line)
                    if match:
                        start_str = " ".join(match.groups())
                        start = datetime.strptime(start_str, "%I:%M %p %d/%m/%Y")
                        data["start"] = self.dt2ts(start)
                elif line.startswith("End time:"):
                    match = re.search("End time: (.*) \(local time\) (\d+/\d+/\d+)", line)
                    if match:
                        end_str = " ".join(match.groups())
                        end = datetime.strptime(end_str, "%I:%M %p %d/%m/%Y")
                        data["end"] = self.dt2ts(end)
                elif line.startswith("Work order number:"):
                    match = re.search("Work order number: (.*)", line)
                    if match:
                        data["maintenance_id"] = match.group(1)
                elif line.startswith("Order ID(s) impacted:"):
                    data["circuits"] = []
                    match = re.search("Order ID\(s\) impacted: (.*)", line)
                    for circuit_id in match.group(1).split(","):
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.lstrip()))
            break  # only need first <div>

    def parse_title(self, title_results: ResultSet, data: Dict):
        """Parse <title> tag."""
        for title in title_results:
            if title.text.startswith("Correction"):
                data["status"] = Status("RE-SCHEDULED")
            elif "Planned" in title.text:
                data["status"] = Status("CONFIRMED")
