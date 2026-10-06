"""Cirion parser.

Based off Lumen parser as Cirion uses forked Lumen code-base.
"""

import logging
import re
from copy import deepcopy
from typing import Dict

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserCirion1(Html):
    """Notifications Parser for Cirion notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        maintenances = []
        data = {}
        self.parse_spans(soup.find_all("span"), data)
        self.parse_tables(soup.find_all("table"), data)

        # Iterates over multiple windows and duplicates other maintenance info to a new dictionary while also updating start and end times for the specific window.
        for window in data["windows"]:
            maintenance = deepcopy(data)
            maintenance["start"], maintenance["end"] = window
            del maintenance["windows"]
            maintenances.append(maintenance)

        # Deleting the key after we are finished checking for multiple windows and duplicating data.
        del data["windows"]

        return maintenances

    def parse_spans(self, spans: ResultSet, data: Dict):
        """Parse Span tag.

        Note: Cirion maintenance email doesn't include an "easy" 1-line summary text, skipped for now.
        """
        for line in spans:
            if isinstance(line, bs4.element.Tag):
                line_text = line.text.lower().strip()

                # Find maintenance_id based on CHG[0-9] (7 digits) pattern
                if re.findall(r"CHG\d{7}", line.text.strip()):
                    data["maintenance_id"] = line.text.strip()
                # Maintenance status below
                elif "this maintenance is scheduled" in line_text:
                    data["status"] = Status("CONFIRMED")
                elif "this maintenance is implement" in line_text:
                    data["status"] = Status("IN-PROCESS")
                elif "this maintenance is closed" in line_text:
                    data["status"] = Status("COMPLETED")

    def parse_tables(self, tables: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse Table tag."""
        # Initialise multiple windows list that will be used in parse_html
        data["windows"] = []

        circuits = []
        for table in tables:
            cells = table.find_all("td")
            if not cells:
                continue
            if cells[0].string == "Start" and cells[1].string == "End":
                num_columns = 2
                for idx in range(num_columns, len(cells), num_columns):
                    if "Greenwich Mean Time" in cells[idx].string and "Greenwich Mean Time" in cells[idx + 1].string:
                        start = parser.parse(cells[idx].string.split("(Greenwich Mean Time)")[0])
                        start_ts = self.dt2ts(start)
                        end = parser.parse(cells[idx + 1].string.split("(Greenwich Mean Time)")[0])
                        end_ts = self.dt2ts(end)
                        data["windows"].append((start_ts, end_ts))
                        break

            elif cells[0].string == "Customer Name":
                num_columns = 1
                if len(cells) % 8 == 0:
                    num_columns = 8
                else:
                    logger.error("Unexpected table format: %s", cells)

                for idx in range(num_columns, len(cells), num_columns):
                    # Account and Status are defined per Circuit ID but we understand that are consistent
                    if "account" not in data:
                        data["account"] = cells[idx].string

                    data_circuit = {}

                    # The table can include "Circuit ID" or "Alt Circuit ID" as columns +1 and +2.
                    # Use the Alt Circuit ID if available (Cirion uses this primarily in their portal as the service ID), else the Circuit ID if available
                    circuit_id = cells[idx + 2].string
                    if circuit_id in ("_", "N/A"):
                        circuit_id = cells[idx + 1].string
                    if circuit_id not in ("_", "N/A"):
                        data_circuit["circuit_id"] = circuit_id

                    impact = cells[idx + 6].string
                    if "outage" in impact.lower():
                        data_circuit["impact"] = Impact("OUTAGE")
                        circuits.append(CircuitImpact(**data_circuit))
                data["circuits"] = circuits
