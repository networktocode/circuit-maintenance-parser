"""GTT parser."""
import logging
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserGTT1(Html):
    """Notifications Parser for GTT notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_tables(soup.find_all("table"), data)
            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_tables(self, tables, data):
        """Parse HTML tables."""
        for table in tables:
            for td_element in table.find_all("td"):
                if "Planned Work Notification" in td_element.text:
                    data["maintenance_id"], status = td_element.text.strip().split(": ")[1].split(" - ")
                    if status == "Reminder":
                        data["status"] = Status["CONFIRMED"]
                    elif status == "Update":
                        data["status"] = Status["RE_SCHEDULED"]
                    elif status == "Cancelled":
                        data["status"] = Status["CANCELLED"]
                        data["start"] = 0
                        data["end"] = 1
                elif "Start" in td_element.text:
                    start = parser.parse(td_element.next_sibling.next_sibling.text)
                    data["start"] = self.dt2ts(start)
                elif "End" in td_element.text:
                    end = parser.parse(td_element.next_sibling.next_sibling.text)
                    data["end"] = self.dt2ts(end)
            num_columns = len(table.find_all("th"))
            if num_columns:
                data["circuits"] = []
                cells = table.find_all("td")
                for idx in range(0, len(cells), num_columns):
                    data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=cells[1].text.strip()))
                    data["account"] = cells[2].text.strip()
