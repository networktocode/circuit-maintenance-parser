"""Colt parser."""

import logging
import re
import csv
import io
import base64

from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.parser import Csv
from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.output import Status, Impact, CircuitImpact
from circuit_maintenance_parser.parser import ICal

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class ICalParserColt1(ICal):
    """Colt Notifications Parser based on ICal notifications."""

    def parse(self, raw: bytes):
        """Method that returns a list of Maintenance objects."""
        result = []

        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(raw))
        except ValueError:
            gcal = Calendar.from_ical(raw)

        if not gcal:
            raise ParserError("Not a valid iCalendar data received")

        for component in gcal.walk():
            if component.name == "VEVENT":
                maintenance_id = ""
                account = ""

                summary_match = re.search(
                    r"^.*?[-]\s(?P<maintenance_id>CRQ[\S]+).*?,\s*(?P<account>\d+)$", str(component.get("SUMMARY"))
                )
                if summary_match:
                    maintenance_id = summary_match.group("maintenance_id")
                    account = summary_match.group("account")

                data = {
                    "account": account,
                    "maintenance_id": maintenance_id,
                    "status": Status("CONFIRMED"),
                    "start": round(component.get("DTSTART").dt.timestamp()),
                    "end": round(component.get("DTEND").dt.timestamp()),
                    "stamp": round(component.get("DTSTAMP").dt.timestamp()),
                    "summary": str(component.get("SUMMARY")),
                    "sequence": int(component.get("SEQUENCE")),
                }
                result.append(data)

        return result


class CsvParserColt1(Csv):
    """Colt Notifications partial parser for circuit-ID's in CSV notifications."""

    @staticmethod
    def parse_csv(raw):
        """Execute parsing."""
        data = {"circuits": []}
        with io.StringIO(raw.decode("utf-16")) as csv_data:
            parsed_csv = csv.DictReader(csv_data, dialect=csv.excel_tab)
            for row in parsed_csv:
                data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=row["Circuit ID"].strip()))
        return [data]
