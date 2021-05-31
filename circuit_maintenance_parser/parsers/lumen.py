"""Lumen parser."""
import logging
from typing import Dict

import dateutil.parser as parser
import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.errors import ParsingError
from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks,no-member, too-many-branches


logger = logging.getLogger(__name__)


class ParserLumen(Html):
    """Notifications Parser for Lumen notifications."""

    provider_type: str = "lumen"

    # Default values for Lumen notifications
    _default_provider = "lumen"
    _default_organizer = "smc@lumen.com"

    def parse_html(self, soup, data):
        """Execute parsing."""
        try:
            self.parse_spans(soup.find_all("span"), data)
            self.parse_tables(soup.find_all("table"), data)

        except Exception as exc:
            raise ParsingError from exc

    def parse_spans(self, spans: ResultSet, data: Dict):
        """Parse Span tag."""
        for line in spans:
            if isinstance(line, bs4.element.Tag):
                if line.text.lower().strip().startswith("scheduled maintenance window #:"):
                    data["maintenance_id"] = line.text.lower().strip().split("#: ")[-1]
                elif line.text.lower().strip().startswith("summary:"):
                    for sibling in line.next_siblings:
                        text = sibling.text if isinstance(sibling, bs4.element.Tag) else sibling
                        if text.strip() != "":
                            data["summary"] = text.strip()
                            break
                elif line.text.lower().strip().startswith("updates:"):
                    for sibling in line.next_siblings:
                        text = sibling.text if isinstance(sibling, bs4.element.Tag) else sibling
                        if text.strip() != "":
                            if "The scheduled maintenance work has begun" in text.strip():
                                data["status"] = "IN-PROCESS"
                            if "GMT" in text.strip():
                                stamp = parser.parse(text.strip().split(" GMT")[0])
                                data["stamp"] = self.dt2ts(stamp)
                            break

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag."""
        circuits = []
        for table in tables:
            cells = table.find_all("td")
            if cells[0].string == "Start" and cells[1].string == "End":
                num_columns = 2
                num_rows = int(len(cells) / num_columns - 1)
                for idx in range(1, num_rows + 1):
                    if "GMT" in cells[idx * num_columns].string and "GMT" in cells[idx * num_columns + 1].string:
                        start = parser.parse(cells[idx * num_columns].string.split(" GMT")[0])
                        data["start"] = self.dt2ts(start)
                        end = parser.parse(cells[idx * num_columns + 1].string.split(" GMT")[0])
                        data["end"] = self.dt2ts(end)
                        break

            elif cells[0].string == "Customer Name":
                # There are tables with 8 columns or 9 columns with "Status" at the end
                num_columns = 1
                if len(cells) % 10 == 0:
                    num_columns = 10
                elif len(cells) % 9 == 0:
                    num_columns = 9
                else:
                    logger.error("Unexpected table format: %s", cells)

                num_rows = int(len(cells) / num_columns - 1)
                for idx in range(1, num_rows + 1):
                    # Account and Status are defined per Circuit ID but we understand that are consistent
                    if "account" not in data:
                        data["account"] = cells[idx * num_columns].string
                    if num_columns == 10:
                        if cells[idx * num_columns + 9].string == "Completed":
                            data["status"] = Status("COMPLETED")

                    data_circuit = {}
                    data_circuit["circuit_id"] = cells[idx * num_columns + 1].string
                    impact = cells[idx * num_columns + 6].string
                    if "outage" in impact.lower():
                        data_circuit["impact"] = Impact("OUTAGE")
                        circuits.append(CircuitImpact(**data_circuit))
                data["circuits"] = circuits
