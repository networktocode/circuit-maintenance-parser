"""Megaport parser."""
import logging
import re
from typing import Dict

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status


logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class HtmlParserMegaport1(Html):
    """Notifications Parser for Megaport notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table", attrs={"class": "TextContentContainer"}), data)
        return [data]

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
                if p_text.startswith("This is a reminder"):
                    data["maintenance_id"] = p_elem.find("b").string
                    data["status"] = Status("CONFIRMED")
                elif p_text.startswith("Hi "):
                    re_search = re.search("Hi (.*)", p_text)
                    if re_search is not None:
                        data["account"] = re_search.group(1)
                elif p_text.startswith("Purpose of Maintenance:"):
                    data["summary"] = p_text.split("Purpose of Maintenance: ")[-1]
                elif p_text.startswith("Start Date and Time:"):
                    re_search = re.search("Start Date and Time: (.*) UTC", p_text)
                    if re_search:
                        start = parser.parse(re_search.group(1))
                        data["start"] = self.dt2ts(start)
                elif p_text.startswith("End Date and Time:"):
                    re_search = re.search("End Date and Time: (.*) UTC", p_text)
                    if re_search:
                        end = parser.parse(re_search.group(1))
                        data["end"] = self.dt2ts(end)

            circuit_table = tr_elem.find("table")
            if circuit_table and circuit_table.find("th").string == "Service ID":
                data["circuits"] = []
                num_columns = len(circuit_table.find_all("th"))
                cells = circuit_table.find_all("td")
                for idx in range(0, len(cells), num_columns):
                    data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=cells[idx].a.string))

                # Once we have all the data we drop because other tables could have object that don't implement some
                # of the used methods
                break
