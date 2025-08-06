"""Telstra parser."""

import logging
import re
from typing import Dict, List

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

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
            for td_element in table.find_all("td"):
                # TODO: We should find a more consistent way to parse the status of a maintenance note
                td_text = td_element.text.lower()
                if "maintenance has been scheduled" in td_text:
                    data["status"] = Status("CONFIRMED")
                elif "this is a reminder notification to notify that a planned maintenance" in td_text:
                    data["status"] = Status("CONFIRMED")
                elif "has been completed" in td_text:
                    data["status"] = Status("COMPLETED")
                elif "has been amended" in td_text:
                    data["status"] = Status("RE-SCHEDULED")
                elif "has been withdrawn" in td_text or "has been cancelled" in td_text:
                    data["status"] = Status("CANCELLED")
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


class HtmlParserTelstra2(Html):
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
            elif strong_text == "Maintenance details":
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
            for span_element in table.find_all("span"):
                span_text = span_element.text.lower()
                if "planned maintenance to our network infrastructure" in span_text:
                    data["status"] = Status("CONFIRMED")
                elif "emergency maintenance to our network infrastructure" in span_text:
                    data["status"] = Status("CONFIRMED")
                elif "has been rescheduled" in span_text:
                    data["status"] = Status("RE-SCHEDULED")
                elif "has been completed successfully" in span_text:
                    data["status"] = Status("COMPLETED")
                elif (
                    "did not proceed" in span_text
                    or "has been withdrawn" in span_text
                    or "has been cancelled" in span_text
                ):
                    data["status"] = Status("CANCELLED")
                elif "was unsuccessful" in span_text:
                    data["status"] = Status("CANCELLED")
                else:
                    continue
                break
            self.add_maintenance_data(table, data)
            break
