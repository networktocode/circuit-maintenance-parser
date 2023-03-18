"""Lumen parser."""
import logging
from typing import Dict

from copy import deepcopy
from dateutil import parser
import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserLumen1(Html):
    """Notifications Parser for Lumen notifications."""

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
        """Parse Span tag."""
        for line in spans:
            if isinstance(line, bs4.element.Tag):
                line_text = line.text.lower().strip()
                if line_text.startswith("scheduled maintenance #:") or line_text.startswith(
                    "scheduled maintenance window #:"
                ):
                    data["maintenance_id"] = line_text.split("#: ")[-1]
                elif line_text.startswith("summary:"):
                    siblings = line.next_siblings
                    if not line.next_sibling:
                        siblings = line.parent.next_sibling
                    for sibling in siblings:
                        text_sibling = sibling.text.strip() if isinstance(sibling, bs4.element.Tag) else sibling.strip()
                        if text_sibling != "":
                            data["summary"] = text_sibling
                            break
                elif line_text.startswith("updates:"):
                    for sibling in line.next_siblings:
                        text_sibling = sibling.text.strip() if isinstance(sibling, bs4.element.Tag) else sibling.strip()
                        if text_sibling != "":
                            if (
                                "This maintenance is scheduled" in text_sibling
                                or "The scheduled maintenance work has begun" in text_sibling
                            ):
                                data["status"] = Status("IN-PROCESS")
                            if "GMT" in text_sibling:
                                stamp = parser.parse(text_sibling.split(" GMT")[0])
                                data["stamp"] = self.dt2ts(stamp)
                            break

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
                    if "GMT" in cells[idx].string and "GMT" in cells[idx + 1].string:
                        start = parser.parse(cells[idx].string.split(" GMT")[0])
                        start_ts = self.dt2ts(start)
                        end = parser.parse(cells[idx + 1].string.split(" GMT")[0])
                        end_ts = self.dt2ts(end)
                        data["windows"].append((start_ts, end_ts))
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

                for idx in range(num_columns, len(cells), num_columns):
                    # Account and Status are defined per Circuit ID but we understand that are consistent
                    if "account" not in data:
                        data["account"] = cells[idx].string
                    if num_columns == 10:
                        status_string = cells[idx + 9].string
                        if status_string == "Completed":
                            data["status"] = Status("COMPLETED")
                        elif status_string == "Postponed":
                            data["status"] = Status("RE-SCHEDULED")
                        elif status_string in ["Not Completed", "Cancelled"]:
                            data["status"] = Status("CANCELLED")
                        elif status_string == "Alternate Night":
                            data["status"] = Status("RE-SCHEDULED")
                    elif "status" not in data:
                        # Update to an existing ticket may not include an update to the status - make a guess
                        data["status"] = "CONFIRMED"

                    data_circuit = {}

                    # The table can include "Circuit ID" or "Alt Circuit ID" as columns +1 and +2.
                    # Use the Circuit ID if available, else the Alt Circuit ID if available
                    circuit_id = cells[idx + 1].string
                    if circuit_id in ("_", "N/A"):
                        circuit_id = cells[idx + 2].string
                    if circuit_id not in ("_", "N/A"):
                        data_circuit["circuit_id"] = circuit_id

                    impact = cells[idx + 6].string
                    if "outage" in impact.lower():
                        data_circuit["impact"] = Impact("OUTAGE")
                        circuits.append(CircuitImpact(**data_circuit))
                data["circuits"] = circuits
