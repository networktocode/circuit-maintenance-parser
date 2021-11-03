"""Colt parser."""

import logging
import re
import csv
import io

from dateutil import parser
from circuit_maintenance_parser.output import Status, Impact, CircuitImpact
from circuit_maintenance_parser.parser import EmailSubjectParser, Csv

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class CsvParserColt1(Csv):
    """Colt Notifications partial parser in CSV notifications."""

    @staticmethod
    def parse_csv(raw):
        """Execute parsing."""
        data = {"circuits": []}
        with io.StringIO(raw.decode("utf-16")) as csv_data:
            parsed_csv = csv.DictReader(csv_data, dialect=csv.excel_tab)
            for row in parsed_csv:
                data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=row["Circuit ID"].strip()))
                if not data.get("account"):
                    search = re.search(r"\d+", row["OCN"].strip())
                    if search:
                        data["account"] = search.group()
        return [data]


class SubjectParserColt1(EmailSubjectParser):
    """Subject parser for Colt notifications."""

    def parse_subject(self, subject):
        """Parse subject.

        Example:
        - [ EXTERNAL ] MAINTENANCE ALERT: CRQ1-12345678 24/10/2021 04:00:00 GMT - 24/10/2021 11:00:00 GMT is about to START
        - [ EXTERNAL ] MAINTENANCE ALERT: CRQ1-12345678 31/10/2021 00:00:00 GMT - 31/10/2021 07:30:00 GMT - COMPLETED
        """
        data = {}
        search = re.search(
            r"\[.+\](.+).+?(CRQ\w+-\w+).+?(\d+/\d+/\d+\s\d+:\d+:\d+\s[A-Z]+).+?(\d+/\d+/\d+\s\d+:\d+:\d+\s[A-Z]+).+?([A-Z]+)",
            subject,
        )
        if search:
            data["maintenance_id"] = search.group(2)
            data["start"] = self.dt2ts(parser.parse(search.group(3)))
            data["end"] = self.dt2ts(parser.parse(search.group(4)))
            if search.group(5) == "START":
                data["status"] = Status("IN-PROCESS")
            elif search.group(5) == "COMPLETED":
                data["status"] = Status("COMPLETED")
            else:
                data["status"] = Status("CONFIRMED")
            data["summary"] = subject
        return [data]
