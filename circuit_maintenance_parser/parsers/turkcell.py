"""Turkcell parser."""
import logging
import re
from typing import Dict

from dateutil import parser
import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserTurkcell1(Html):
    """Notifications Parser for Turkcell notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_tables(soup.find_all("table"), data)
            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_tables(self, tables, data):
        """Parse tables."""
        # Main table
        td_elements = tables[0].find_all("td")
        for idx, td in enumerate(td_elements):
            if "Dear Customer" in td.text.strip():
                if "planned" in td.text.strip():
                    data["status"] = Status["CONFIRMED"]
                else:
                    data["status"] = Status["CONFIRMED"]
            if "Maintenance Number" in td.text.strip():
                data["maintenance_id"] = td_elements[idx + 1].text.strip()
            elif "Start" in td.text.strip():
                data["start"] = self.dt2ts(parser.parse(td_elements[idx + 1].text.strip()))
            elif "End" in td.text.strip():
                data["end"] = self.dt2ts(parser.parse(td_elements[idx + 1].text.strip()))
            elif "Impact of the maintenance" in td.text.strip():
                data["summary"] = td_elements[idx + 1].span.text.strip()
                if len(tables) == 1:
                    data["circuits"] = []
                    p_elements = td_elements[idx + 1].find_all("p")
                    for element in p_elements:
                        # Example match:
                        #   Eth-Trunk1.1               up      up       111111111111111|01-CUSTOMER|LOCATION|LINK
                        if re.match(r".+[ \t]([0-1]+\|.+\|.+\|.+)", element.text.strip()):
                            groups = re.search(r".+[ \t]([0-1]+\|.+\|.+\|.+)", element.text.strip())
                            details = groups.group(1).split("|")
                            data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=details[0]))
                            data["account"] = details[1]

        # Circuit table
        # Possibility that there could be a table inside the first table.
        if len(tables) == 2:
            tr_elements = tables[1].find_all("tr")
            data["circuits"] = []
            for tr in tr_elements:
                line = tr.text.strip().split("\n\n\n")
                data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=line[0]))
                data["account"] = line[1]
