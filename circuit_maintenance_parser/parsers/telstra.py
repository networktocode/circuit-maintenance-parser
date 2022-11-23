"""Telstra parser."""
import logging
from typing import Dict, List
import re
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

    def add_maintenance_data(self, table: ResultSet, data: Dict):
        """Populate data dict."""
        for strong_element in table.find_all("strong"):
            if not strong_element.string:
                continue
            strong_text = strong_element.string.strip()
            strong_sibling = strong_element.next_sibling.next_sibling
            if strong_text == "Reference number":
                data["maintenance_id"] = strong_sibling.string.strip()
            elif strong_text == "Start time":
                text_start = strong_sibling.string
                regex = re.search(r"\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_start)
                if regex is not None:
                    start = parser.parse(regex.group())
                    data["start"] = self.dt2ts(start)
                else:
                    data["start"] = "Not defined"
            elif strong_text == "End time":
                text_end = strong_sibling.string
                regex = re.search(r"\d{2}\s[a-zA-Z]{3}\s\d{4}\s\d{2}[:]\d{2}[:]\d{2}", text_end)
                if regex is not None:
                    end = parser.parse(regex.group())
                    data["end"] = self.dt2ts(end)
                else:
                    data["end"] = "is not defined"
            elif strong_text == "Service/s under maintenance":
                data["circuits"] = []
                # TODO: This split is just an assumption of the multiple service, to be checked with more samples
                impacted_circuits = strong_sibling.text.split(", ")
                for circuit_id in impacted_circuits:
                    data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.strip()))
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

    def parse_tables(self, tables: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse Table tag."""
        for table in tables:
            for p_element in table.find_all("p"):
                # TODO: We should find a more consistent way to parse the status of a maintenance note
                p_text = p_element.text.lower()
                if "attention" in p_text:
                    regex = re.search("[^attention ].*", p_text.strip())
                    if regex is not None:
                        data["account"] = regex.group()
                    else:
                        data["account"] = "not Found"
                if "maintenance has been scheduled" in p_text:
                    data["status"] = Status("CONFIRMED")
                elif "successful" in p_text:
                    data["status"] = Status("COMPLETED")
                elif "this is a note to let you know that we'll soon be doing some network maintenance" in p_text:
                    data["status"] = Status("CONFIRMED")
                elif "has been rescheduled" in p_text:
                    data["status"] = Status("RE-SCHEDULED")
                elif "has been withdrawn" in p_text or "has been cancelled" in p_text:
                    data["status"] = Status("CANCELLED")
                else:
                    continue
                break
            self.add_maintenance_data(table, data)
            break
