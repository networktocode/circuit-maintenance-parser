import logging
from typing import Dict

from bs4.element import ResultSet  # type: ignore


from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status


class HtmlParserTelia1(Html):
    """Notifications Parser for Telia notifications."""

    def parse_html(self, soup, data_base):
        """Execute parsing."""
        data = data_base.copy()
        try:
            self.parse_tables(soup.find_all("table"), data)

            return [data]

        except Exception as exc:
            raise ParsingError from exc

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag"""
        circuits = []
        for table in tables:
            cells = table.find_all("td")
            breakpoint()
