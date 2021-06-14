"""Cogent parser."""
import logging
import re
from typing import Dict
from pytz import timezone, UTC
from datetime import datetime
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status
from circuit_maintenance_parser.util import city_timezone

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
        start_str = ""
        end_str = ""

        for div in divs:
            # if not div.get("class"):
            #     continue
            # div_class = " ".join(div.get("class"))
            # if div_class == "ha":
            #     match = re.search("(.*)[^A-Z\d-]+", div.text)
            #     if match:

            # elif div_class == "a3s aiL":
            for line in div.text.splitlines():
                if line.endswith("Network Maintenance"):
                    data["summary"] = line
                elif line.startswith("Dear"):
                    match = re.search("Dear (.*),", line)
                    if match:
                        data["account"] = match.group(1)
                elif line.startswith("Start time:"):
                    match = re.search("Start time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
                    if match:
                        start_str = " ".join(match.groups())
                elif line.startswith("End time:"):
                    match = re.search("End time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
                    if match:
                        end_str = " ".join(match.groups())
                elif line.startswith("Cogent customers receiving service"):
                    match = re.search(r"[^Cogent].*?((\b[A-Z][a-z\s-]+)+, ([A-Za-z-]+[\s-]))", line)
                    if match:
                        parsed_timezone = city_timezone(match.group(1).strip())
                        local_timezone = timezone(parsed_timezone)
                        # set start time using the local city timezone
                        start = datetime.strptime(start_str, "%I:%M %p %d/%m/%Y")
                        local_time = local_timezone.localize(start)
                        # set start time to UTC
                        utc_start = local_time.astimezone(UTC)
                        data["start"] = self.dt2ts(utc_start)

                        # set end time using the local city timezone
                        end = datetime.strptime(end_str, "%I:%M %p %d/%m/%Y")
                        local_time = local_timezone.localize(end)
                        # set end time to UTC
                        utc_end = local_time.astimezone(UTC)
                        data["end"] = self.dt2ts(utc_end)
                elif line.startswith("Work order number:"):
                    match = re.search("Work order number: (.*)", line)
                    if match:
                        data["maintenance_id"] = match.group(1)
                elif line.startswith("Order ID(s) impacted:"):
                    data["circuits"] = []
                    match = re.search("Order ID\(s\) impacted: (.*)", line)
                    for circuit_id in match.group(1).split(","):
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.lstrip()))
            break

    def parse_title(self, title_results: ResultSet, data: Dict):
        """Parse <title> tag."""
        for title in title_results:
            if title.text.startswith("Correction"):
                data["status"] = Status("RE-SCHEDULED")
            elif "Planned" in title.text:
                data["status"] = Status("CONFIRMED")
