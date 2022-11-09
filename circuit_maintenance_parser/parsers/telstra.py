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
            for td_element in table.find_all("p"):
                # TODO: We should find a more consistent way to parse the status of a maintenance note
                td_text = td_element.text.lower()
                print(td_text)
                if "maintenance has been scheduled" in td_text:
                    data["status"] = Status("CONFIRMED")
                elif "successful" in td_text:
                    data["status"] = Status("COMPLETED")
                elif (
                    "this is a note to let you know that we'll soon be doing some network maintenance"
                    in td_text
                ):
                    data["status"] = Status("CONFIRMED")
                elif "has been rescheduled" in td_text:
                    data["status"] = Status("RE-SCHEDULED")
                elif "has been withdrawn" in td_text or "has been cancelled" in td_text:
                    data["status"] = Status("CANCELLED")
                else:
                    continue
                break
            for th_element in table.find_all("strong"):
                if not th_element.string:
                    continue
                th_text = th_element.string.strip()
                th_sibling = th_element.next_sibling.next_sibling
                data["account"] = "Criteo SA (EMEA)"
                if th_text == "Reference number":
                    data["maintenance_id"] = th_sibling.string
                elif th_text == "Start time":
                    text_start = th_sibling.string
                    regex = re.search(
                        "\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_start
                    )
                    start = parser.parse(regex.group())
                    data["start"] = self.dt2ts(start)
                elif th_text == "End time":
                    text_end = th_sibling.string
                    regex = re.search("\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_end)
                    end = parser.parse(regex.group())
                    data["end"] = self.dt2ts(end)
                elif th_text == "Service/s under maintenance":
                    data["circuits"] = []
                    # TODO: This split is just an assumption of the multiple service, to be checked with more samples
                    impacted_circuits = th_sibling.text.split(", ")
                    for circuit_id in impacted_circuits:
                        data["circuits"].append(
                            CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id)
                        )
                elif th_text == "Maintenance Details":
                    sentences: List[str] = []
                    for element in th_element.next_elements:
                        if element.string == "Reference number":
                            break
                        if element.string and element.string not in ["\n", "", "\xa0"] + sentences:
                            sentences.append(element.string)
                    if sentences:
                        # First sentence containts 'Maintenance Details' so we skip it
                        data["summary"] = ". ".join(sentences[1:])
            break
