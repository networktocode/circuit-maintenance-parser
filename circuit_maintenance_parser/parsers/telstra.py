"""Telstra parser."""
import logging
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserTelstra1(Html):
    """Notifications Parser for Telstra notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag."""
        for table in tables:
            for td_element in table.find_all("td"):
                # TODO: We should find a more consistent way to parse the status of a maintenance note
                if "Planned Maintenance has been scheduled" in td_element.text:
                    data["status"] = Status("CONFIRMED")
                elif "This is a reminder notification to notify that a planned maintenance" in td_element.text:
                    data["status"] = Status("CONFIRMED")
                else:
                    continue
                break
            for th_element in table.find_all("th"):
                if not th_element.string:
                    continue
                th_text = th_element.string.strip()
                th_sibling = th_element.next_sibling.next_sibling
                if th_text == "To:":
                    data["account"] = th_sibling.string
                elif th_text == "Change Reference:":
                    data["maintenance_id"] = th_sibling.string
                elif th_text == "Maintenance Window:":
                    text_dates = th_sibling.string.split("(UTC) to ")
                    start = parser.parse(text_dates[0])
                    data["start"] = self.dt2ts(start)
                    end = parser.parse(text_dates[1].strip("(UTC)"))
                    data["end"] = self.dt2ts(end)
                elif th_text == "Service(s) Impacted:":
                    data["circuits"] = []
                    # TODO: This split is just an assumption of the multiple service, to be checked with more samples
                    impacted_circuits = th_sibling.text.split(", ")
                    for circuit_id in impacted_circuits:
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))
                elif th_text == "Maintenance Details:":
                    sentences: List[str] = []
                    for element in th_element.next_elements:
                        if element.string == "Service(s) Impacted:":
                            break
                        if element.string and element.string not in ["\n", "", "\xa0"] + sentences:
                            sentences.append(element.string)
                    if sentences:
                        # First sentence containts 'Maintenance Details:' so we skip it
                        data["summary"] = ". ".join(sentences[1:])
            break
