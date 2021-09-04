"""Telstra parser."""
import logging
import re
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status, Subject

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class SubjectParserSeaborn1(Subject):
    """PArser for Seaborn subject string."""

    def parse_subject(self, subject, data_base):
        data = data_base.copy()
        try:
            search = re.search(r".+\[## ([0-9]+) ##\].+", subject)
            if search:
                data["account"] = search.group(1)
            return [data]

        except Exception as exc:
            raise ParserError from exc


class HtmlParserSeaborn1(Html):
    """Notifications Parser for Seaborn notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_body(soup, data)
            return [data]

        except Exception as exc:
            raise ParserError from exc

    def parse_body(self, body, data):
        p_elements = body.find_all("p")

        for index, element in enumerate(p_elements):
            if "NOTIFICATION TYPE" in element.text:
                pass
            elif "DESCRIPTION" in element.text:
                pass
            elif "SERVICE IMPACT" in element.text:
                pass
            elif "LOCATION" in element.text:
                pass
            elif "SCHEDULE" in element.text:
                schedule = p_elements[index + 1].text
                start, end = schedule.split(" - ")
                data["start"] = self.dt2ts(parser.parse(start))
                data["end"] = self.dt2ts(parser.parse(end))
                data["status"] = Status("CONFIRMED")
            elif "AFFECTED CIRCUIT" in element.text:
                circuit_id = element.text.split(": ")[1]
                data["circuits"] = [(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))]


class HtmlParserSeaborn2(Html):
    """Notifications Parser for Seaborn notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_body(soup, data)
            return [data]

        except Exception as exc:
            raise ParserError from exc

    def parse_body(self, body, data):
        div_elements = body.find_all("div")
        for element in div_elements:
            if "Be advised" in element.text:
                if "been rescheduled" in element.text:
                    data["status"] = Status["RE_SCHEDULED"]
                elif "been scheduled" in element.text:
                    data["status"] = Status["CONFIRMED"]
            elif "Description" in element.text:
                pass
            elif "Seaborn Ticket" in element.text:
                data["maintenance_id"] = element.text.split(":")[1]
            elif "Start date" in element.text:
                start = element.text.split(": ")[1]
                data["start"] = self.dt2ts(parser.parse(start))
            elif "Finish date" in element.text:
                end = element.text.split(": ")[1]
                data["end"] = self.dt2ts(parser.parse(end))
            elif "Circuit impacted" in element.text:
                circuit_id = self.remove_hex_characters(element.text).split(":")[1]
                data["circuits"] = [(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))]
