"""Telstra parser."""
import logging
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserSeaborn1(Html):
    """Notifications Parser for Seaborn notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_body(soup, data)
            return [data]

        except Exception as exc:
            raise ParsingError from exc

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