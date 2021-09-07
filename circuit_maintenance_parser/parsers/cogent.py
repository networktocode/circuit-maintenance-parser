"""Cogent parser."""
import logging
import re
from typing import Dict
from datetime import datetime
from pytz import timezone, UTC
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status
from circuit_maintenance_parser.utils import city_timezone

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class HtmlParserCogent1(Html):
    """Notifications Parser for Cogent notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_div(soup.find_all("div", class_="a3s aiL"), data)
        self.parse_title(soup.find_all("title"), data)
        return [data]

    def parse_div(self, divs: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse <div> tag."""
        start_str = ""
        end_str = ""

        for div in divs:
            for line in div.text.splitlines():
                if line.endswith("Network Maintenance"):
                    data["summary"] = line
                elif line.startswith("Dear"):
                    match = re.search(r"Dear (.*),", line)
                    if match:
                        data["account"] = match.group(1)
                elif line.startswith("Start time:"):
                    match = re.search(r"Start time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
                    if match:
                        start_str = " ".join(match.groups())
                elif line.startswith("End time:"):
                    match = re.search(r"End time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
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
                        logger.info(
                            "Mapped start time %s at %s (%s), to %s (UTC)",
                            start_str,
                            match.group(1).strip(),
                            local_timezone,
                            utc_start,
                        )
                        # set end time using the local city timezone
                        end = datetime.strptime(end_str, "%I:%M %p %d/%m/%Y")
                        local_time = local_timezone.localize(end)
                        # set end time to UTC
                        utc_end = local_time.astimezone(UTC)
                        data["end"] = self.dt2ts(utc_end)
                        logger.info(
                            "Mapped end time %s at %s (%s), to %s (UTC)",
                            end_str,
                            match.group(1).strip(),
                            local_timezone,
                            utc_end,
                        )
                elif line.startswith("Work order number:"):
                    match = re.search("Work order number: (.*)", line)
                    if match:
                        data["maintenance_id"] = match.group(1)
                elif line.startswith("Order ID(s) impacted:"):
                    data["circuits"] = []
                    match = re.search(r"Order ID\(s\) impacted: (.*)", line)
                    if match:
                        for circuit_id in match.group(1).split(","):
                            data["circuits"].append(
                                CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.strip())
                            )
            break

    @staticmethod
    def parse_title(title_results: ResultSet, data: Dict):
        """Parse <title> tag."""
        for title in title_results:
            if title.text.startswith("Correction"):
                data["status"] = Status("RE-SCHEDULED")
            elif "Planned" in title.text:
                data["status"] = Status("CONFIRMED")
