"""Zayo parser."""
import logging
from typing import Dict

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from dateutil import parser

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks,no-member, too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserZayo1(Html):
    """Notifications Parser for Zayo notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_bs(soup.find_all("b"), data)
        self.parse_tables(soup.find_all("table"), data)

        if data:
            if "account" not in data:
                data["account"] = "unknown"
            if "status" not in data:
                text = soup.get_text()
                if "will be commencing momentarily" in text:
                    data["status"] = Status("IN-PROCESS")
                elif "has been completed" in text:
                    data["status"] = Status("COMPLETED")

        return [data]

    def parse_bs(self, btags: ResultSet, data: dict):
        """Parse B tag."""
        for line in btags:
            if isinstance(line, bs4.element.Tag):
                if line.text.lower().strip().startswith("maintenance ticket #:"):
                    data["maintenance_id"] = self.clean_line(line.next_sibling)
                elif "serves as official notification" in line.text.lower():
                    if "will be performing maintenance" in line.text.lower():
                        data["status"] = Status("CONFIRMED")
                    elif "has cancelled" in line.text.lower():
                        data["status"] = Status("CANCELLED")
                # TODO: some Zayo notifications may include multiple activity dates. How best to handle this?
                # 1st Activity Date
                # 01-Nov-2021 00:01 to 01-Nov-2021 05:00 ( Mountain )
                # 01-Nov-2021 06:01 to 01-Nov-2021 11:00 ( GMT )
                #
                # 2nd Activity Date
                # 02-Nov-2021 00:01 to 02-Nov-2021 05:00 ( Mountain )
                # 02-Nov-2021 06:01 to 02-Nov-2021 11:00 ( GMT )
                #
                # 3rd Activity Date
                # 03-Nov-2021 00:01 to 03-Nov-2021 05:00 ( Mountain )
                # 03-Nov-2021 06:01 to 03-Nov-2021 11:00 ( GMT )
                elif "activity date" in line.text.lower():
                    logger.info("Found 'activity date': %s", line.text)
                    for sibling in line.next_siblings:
                        text = sibling.text if isinstance(sibling, bs4.element.Tag) else sibling
                        logger.debug("Checking for GMT date/timestamp in sibling: %s", text)
                        if "( GMT )" in text:
                            window = self.clean_line(sibling).strip("( GMT )").split(" to ")
                            start = parser.parse(window.pop(0))
                            data["start"] = self.dt2ts(start)
                            end = parser.parse(window.pop(0))
                            data["end"] = self.dt2ts(end)
                            break
                elif line.text.lower().strip().startswith("reason for maintenance:"):
                    data["summary"] = self.clean_line(line.next_sibling)
                # TODO: not all Zayo notifications include "date notice sent".
                # Do we need to pull the date from the email headers, or what should we do here?
                elif line.text.lower().strip().startswith("date notice sent:"):
                    stamp = parser.parse(self.clean_line(line.next_sibling))
                    data["stamp"] = self.dt2ts(stamp)
                # TODO: not all Zayo notifications include "customer".
                # Do we need to pull the customer name from the email subject line, or what should we do here?
                elif line.text.lower().strip().startswith("customer:"):
                    data["account"] = self.clean_line(line.next_sibling)

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag."""
        circuits = []
        for table in tables:
            head_row = table.find_all("th")
            if len(head_row) < 5:
                logger.warning("Less table headers than expected: %s", head_row)
                continue

            table_headers = [self.clean_line(line) for line in head_row[:5]]
            expected_headers_ref = (
                ["Circuit Id", "Expected Impact", "A Location CLLI", "Z Location CLLI", "Legacy Circuit Id",],
                ["Circuit Id", "Expected Impact", "A Location Address", "Z Location Address", "Legacy Circuit Id",],
            )
            if all(table_headers != expected_headers for expected_headers in expected_headers_ref):
                logger.warning("Table headers are not as expected: %s", head_row)
                continue

            data_rows = table.find_all("td")
            if len(data_rows) % 5 != 0:
                raise AssertionError("Table format is not correct")
            number_of_circuits = int(len(data_rows) / 5)
            for idx in range(number_of_circuits):
                data_circuit = {}
                data_circuit["circuit_id"] = self.clean_line(data_rows[0 + 5 * idx])
                impact = self.clean_line(data_rows[1 + 5 * idx])
                if "hard down" in impact.lower():
                    data_circuit["impact"] = Impact("OUTAGE")
                elif "no expected impact" in impact.lower():
                    data_circuit["impact"] = Impact("NO-IMPACT")
                circuits.append(CircuitImpact(**data_circuit))
        if circuits:
            data["circuits"] = circuits
