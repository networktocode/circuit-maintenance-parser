"""Verizon parser."""
import logging
import re
from typing import Dict
from dateutil import parser
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class HtmlParserVerizon1(Html):
    """Notifications Parser for Verizon notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        logger.debug("Parsing Verizon HTML notification.")
        self.parse_tables(soup.find_all("table"), data)
        self.parse_p(soup.find_all("p"), data)
        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse <table> tag."""
        maintenance_table = tables[0]
        circuit_table = tables[1]
        circuits = []

        data["status"] = Status("CONFIRMED")
        for row in maintenance_table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            cells_text = []
            for cell in cells:
                p_tags = cell.find_all("p")
                cell_text = ""
                for p_tag in p_tags:
                    cell_text += p_tag.text.strip()
                cells_text.append(cell_text)
            if not cells_text:
                continue
            if cells_text[0].startswith("Description of Maintenance"):
                data["summary"] = cells_text[1]
            elif cells_text[0].startswith("Verizon MASTARS Request number:"):
                data["maintenance_id"] = cells_text[1]
            elif cells_text[0].startswith("Attention:"):
                if "maintenance was not completed" in cells_text[0]:
                    data["status"] = Status("CANCELLED")
            elif cells_text[0].startswith("Maintenance Date/Time (GMT):"):
                maintenance_time = cells_text[1].split("-")
                start = parser.parse(maintenance_time[0].strip())
                end = parser.parse(maintenance_time[1].strip())
                data["start"] = self.dt2ts(start)
                data["end"] = self.dt2ts(end)

        for row in circuit_table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            cells_text = [cell.string.strip() for cell in cells if cell.string]
            if not cells_text or cells_text[0].startswith("Company Name"):
                continue
            circuit_id = cells_text[1]
            circuits.append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))
        data["circuits"] = circuits

    @staticmethod
    def parse_p(p_tags: ResultSet, data: Dict):
        """Parse <p> tag."""
        for p_tag in p_tags:
            p_text = p_tag.text.strip()
            match = re.match(r"Dear (.*),", p_text)
            if match:
                data["account"] = match.group(1)
                break
