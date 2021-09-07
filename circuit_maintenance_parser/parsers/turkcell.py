"""Turkcell parser."""
import logging
import re
from typing import Dict

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class HtmlParserTurkcell1(Html):
    """Notifications Parser for Turkcell notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse tables.

        Format 1 supported here (all information in a single table):
            <table>
                <tr>
                    <td>Dear Customer ... planned ...</td>
                    <td>...</td>
                </tr>
                <tr>
                    <td>Maintenance Number</td>
                    <td>123456789</td>
                </tr>
                <tr>
                    <td>Start</td>
                    <td>2021-08-31 01:02:03</td>
                </td>
                <tr>
                    <td>End</td>
                    <td>2021-08-31 01:02:04</td>
                </td>
                <tr>
                    <td>Impact of the maintenance</td>
                    <td>
                        <p>CIRCUIT1|01-CUSTOMER|LOCATION|LINK</p>
                        <p>CIRCUIT2|01-CUSTOMER|LOCATION|LINK</p>
                    </td>
                </td>
            </table>

        Format #2 supported here (one table for general information, a separate table listing impacted circuits):
            <table>
                <tr>
                    <td>Dear Customer ... planned ...</td>
                    <td>...</td>
                </tr>
                <tr>
                    <td>Maintenance Number</td>
                    <td>123456789</td>
                </tr>
                <tr>
                    <td>Start</td>
                    <td>2021-08-31 01:02:03</td>
                </td>
                <tr>
                    <td>End</td>
                    <td>2021-08-31 01:02:04</td>
                </td>
                <tr>
                    <td>Impact of the maintenance</td>
                    <table>
                        <tr>
                            <td>Circuit 1</td>
                            <td>Custom Name</td>
                            <td>Down</td>
                        </tr>
                        <tr>
                            <td>Circuit 2</td>
                            <td>Custom Name</td>
                            <td>Down</td>
                        </tr>
                    </table>
                </td>
            </table>
        """
        # Main table
        td_elements = tables[0].find_all("td")
        for idx, td_element in enumerate(td_elements):
            if "Dear Customer" in td_element.text.strip():
                if "planned" in td_element.text.strip():
                    data["status"] = Status["CONFIRMED"]
                else:
                    data["status"] = Status["CONFIRMED"]
            if "Maintenance Number" in td_element.text.strip():
                data["maintenance_id"] = td_elements[idx + 1].text.strip()
            elif "Start" in td_element.text.strip():
                data["start"] = self.dt2ts(parser.parse(td_elements[idx + 1].text.strip()))
            elif "End" in td_element.text.strip():
                data["end"] = self.dt2ts(parser.parse(td_elements[idx + 1].text.strip()))
            elif "Impact of the maintenance" in td_element.text.strip():
                data["summary"] = td_elements[idx + 1].span.text.strip()
                if len(tables) == 1:
                    data["circuits"] = []
                    p_elements = td_elements[idx + 1].find_all("p")
                    for element in p_elements:
                        # Example match:
                        #   Eth-Trunk1.1               up      up       111111111111111|01-CUSTOMER|LOCATION|LINK
                        groups = re.search(r".+[ \t]([0-1]+\|.+\|.+\|.+)", element.text.strip())
                        if groups:
                            details = groups.group(1).split("|")
                            data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=details[0]))
                            data["account"] = details[1]

                # Circuit table
                # Possibility that there could be a table inside the first table.
                elif len(tables) == 2:
                    tr_elements = tables[1].find_all("tr")
                    data["circuits"] = []
                    for tr_element in tr_elements:
                        line = tr_element.text.strip().split("\n\n\n")
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=line[0]))
                        data["account"] = line[1]
