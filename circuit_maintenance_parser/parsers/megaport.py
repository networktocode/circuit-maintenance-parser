"""Megaport parser."""

import logging
import re
from typing import Dict

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

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
            p_summary = False
            for p_elem in td_elem.find_all("p"):
                p_text = p_elem.text.strip()
                if not p_text:
                    continue
                if p_text.startswith("This is a reminder") or p_text.startswith("Please be advised that"):
                    data["maintenance_id"] = p_elem.find("b").string
                    data["status"] = Status("CONFIRMED")
                elif p_text.startswith("Hi "):
                    re_search = re.search("Hi (.*)", p_text)
                    if re_search is not None:
                        data["account"] = re_search.group(1)
                elif p_text.startswith("Purpose of Maintenance:"):
                    # When p_text only contains "Purpose of Maintenance:"; assume that the purpose is given in the next paragraph
                    if p_text == "Purpose of Maintenance:":
                        p_summary = True
                    else:
                        data["summary"] = p_text.split("Purpose of Maintenance: ")[-1]
                elif p_summary:
                    # This paragraph contains contents for "purpose of maintenance"
                    data["summary"] = p_text
                    p_summary = False
                elif p_text.startswith("Start Date and Time:"):
                    # Megaport uses different formats in their initial maintenance announcement email and reminder email. In their reminder email they split start and end date across paragraphs
                    re_search = re.search("Start Date and Time: (.*) UTC End Date and Time: (.*) UTC", p_text)
                    if re_search:
                        data["start"] = self.dt2ts(parser.parse(re_search.group(1)))
                        data["end"] = self.dt2ts(parser.parse(re_search.group(2)))
                    # for their reminder email, only look for start date
                    else:
                        re_search = re.search("Start Date and Time: (.*) UTC", p_text)
                        if re_search:
                            data["start"] = self.dt2ts(parser.parse(re_search.group(1)))
                elif p_text.startswith("End Date and Time:"):
                    re_search = re.search("End Date and Time: (.*) UTC", p_text)
                    if re_search:
                        data["end"] = self.dt2ts(parser.parse(re_search.group(1)))

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
