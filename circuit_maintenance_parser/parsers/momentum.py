"""Momentum parser."""
import logging
from typing import Dict, List

from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserMomentum1(Html):
    """Notifications Parser for Momentum notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_body(soup.find_all("p"), data)

            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_body(self, p_elements, data):
        for element in p_elements:
            text = element.text.encode('ascii', errors='ignore').decode("utf-8")
            for line in text.splitlines():
                if "Account" in line:
                    data["account"] = line.split(": ")[1]
                elif "Circuit ID" in line:
                    data["circuits"] = []
                    for circuit_id in line.split(": ")[1].split(", "):
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))
                elif "Maintenance start date/time" in line:
                    data["start"] = self.dt2ts(parser.parse(line.split("time:")[1]))
                elif "Maintenance finish date/time" in line:
                    data["end"] = self.dt2ts(parser.parse(line.split("time:")[1]))
