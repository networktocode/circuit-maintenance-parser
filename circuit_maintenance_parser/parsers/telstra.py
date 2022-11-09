"""Telstra parser."""
import logging
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status
import re

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserTelstra1(Html):
    """Notifications Parser for Telstra notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse Table tag."""
        for table in tables:
            for p_element in table.find_all("p"):
                # TODO: We should find a more consistent way to parse the status of a maintenance note
                p_text = p_element.text.lower()
                if "maintenance has been scheduled" in p_text:
                    data["status"] = Status("CONFIRMED")
                elif "successful" in p_text:
                    data["status"] = Status("COMPLETED")
                elif (
                    "this is a note to let you know that we'll soon be doing some network maintenance"
                    in p_text
                ):
                    data["status"] = Status("CONFIRMED")
                elif "has been rescheduled" in p_text:
                    data["status"] = Status("RE-SCHEDULED")
                elif "has been withdrawn" in p_text or "has been cancelled" in p_text:
                    data["status"] = Status("CANCELLED")
                else:
                    continue
                break
            for strong_element in table.find_all("strong"):
                if not strong_element.string:
                    continue
                strong_text = strong_element.string.strip()
                strong_sibling = strong_element.next_sibling.next_sibling
                data["account"] = "Criteo SA (EMEA)"
                if strong_text == "Reference number":
                    data["maintenance_id"] = strong_sibling.string
                elif strong_text == "Start time":
                    text_start = strong_sibling.string
                    regex = re.search(
                        "\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_start
                    )
                    start = parser.parse(regex.group())
                    data["start"] = self.dt2ts(start)
                elif strong_text == "End time":
                    text_end = strong_sibling.string
                    regex = re.search("\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_end)
                    end = parser.parse(regex.group())
                    data["end"] = self.dt2ts(end)
                elif strong_text == "Service/s under maintenance":
                    data["circuits"] = []
                    # TODO: This split is just an assumption of the multiple service, to be checked with more samples
                    impacted_circuits = strong_sibling.text.split(", ")
                    for circuit_id in impacted_circuits:
                        data["circuits"].append(
                            CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id)
                        )
                elif strong_text == "Maintenance Details":
                    sentences: List[str] = []
                    for element in strong_element.next_elements:
                        if element.string == "Reference number":
                            break
                        if element.string and element.string not in ["\n", "", "\xa0"] + sentences:
                            sentences.append(element.string)
                    if sentences:
                        # First sentence containts 'Maintenance Details' so we skip it
                        data["summary"] = ". ".join(sentences[1:])
            break
