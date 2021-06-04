"""Megaport parser."""
import logging
from typing import Dict

import dateutil.parser as parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status


logger = logging.getLogger(__name__)


class ParserMegaport(Html):
    """Notifications Parser for Megaport notifications."""

    provider_type: str = "megaport"

    # Default values for Megaport notifications
    _default_provider = "megaport"
    _default_organizer = "support@megaport.com"

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_tables(soup.find_all("table", attrs={"class": "TextContentContainer"}), data)

            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag."""
        # The interesting table is the second one
        table = tables[1]

        for tr_elem in table.find("tbody").find_all("tr"):
            td_elem = tr_elem.find("td")
            for p_elem in td_elem.find_all("p"):
                p_text = p_elem.text
                if not p_text:
                    continue
                if p_text.startswith("This is a reminder that Planned maintenance"):
                    data["maintenance_id"] = p_elem.find("b").string
                    data["status"] = Status("CONFIRMED")
                elif p_text.startswith("Hi "):
                    data["account"] = p_text.split("Hi ")[-1]
                elif p_text.startswith("Purpose of Maintenance:"):
                    data["summary"] = p_text.split("Purpose of Maintenance: ")[-1]
                elif p_text.startswith("Start Date and Time:"):
                    start = parser.parse(p_text.split("Start Date and Time: ")[-1].strip(" UTC"))
                    data["start"] = self.dt2ts(start)
                elif p_text.startswith("End Date and Time:"):
                    end = parser.parse(p_text.split("End Date and Time: ")[-1].strip(" UTC"))
                    data["end"] = self.dt2ts(end)

            circuit_table = tr_elem.find("table")
            if circuit_table and circuit_table.find("th").string == "Service ID":
                data["circuits"] = []
                num_columns = len(circuit_table.find_all("th"))
                cells = circuit_table.find_all("td")
                for idx in range(0, len(cells), num_columns):
                    data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=cells[idx].a.string))

                return
