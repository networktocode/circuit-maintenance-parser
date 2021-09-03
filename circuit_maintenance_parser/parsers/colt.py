"""Colt parser."""
import logging
import re
import base64
from typing import Dict
from datetime import datetime
from pytz import timezone, UTC
from bs4.element import ResultSet  # type: ignore

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import ValidationError, List
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParsingError, MissingMandatoryFields
from circuit_maintenance_parser.output import Maintenance, Status, Impact, CircuitImpact
from circuit_maintenance_parser.output import ICal

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches


class ICalParserColt(ICal):
    """Colt Notifications Parser based on ICal notifications.
    """

    def parse(self, raw: bytes) -> List[Dict]:
        """Method that returns a list of Maintenance objects."""
        result = []

        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(self.raw))
        except ValueError:
            try:
                gcal = Calendar.from_ical(self.raw)
            except ValueError as exc:
                raise ParsingError from exc

        if not gcal:
            raise ParsingError("Not a valid iCalendar data received")

        try:
            gcal = Calendar.from_ical(self.raw)
            for component in gcal.walk():
                if component.name == "VEVENT":
                    maintenance_id = ""
                    account = ""

                    organizer = (
                        str(component.get("ORGANIZER")) if component.get("ORGANIZER") else self.default_organizer
                    )
                    provider = (
                        str(component.get("X-MAINTNOTE-PROVIDER"))
                        if component.get("X-MAINTNOTE-PROVIDER")
                        else self.default_provider
                    )
                    summary_match = re.search(
                        r"^.*?[-]\s(?P<maintenance_id>CRQ[\S]+).*?,\s*(?P<account>\d+)$", str(component.get("SUMMARY"))
                    )
                    if summary_match:
                        maintenance_id = summary_match.groups("maintenance_id")
                        account = summary_match.groups("account")

                    data = {
                        "circuits": [],
                        "provider": provider,
                        "account": account,
                        "maintenance_id": maintenance_id,
                        # "status": Status(component.get("X-MAINTNOTE-STATUS")),
                        "start": round(component.get("DTSTART").dt.timestamp()),
                        "end": round(component.get("DTEND").dt.timestamp()),
                        "stamp": round(component.get("DTSTAMP").dt.timestamp()),
                        "summary": str(component.get("SUMMARY")),
                        "organizer": organizer,
                        "uid": str(component.get("UID")),
                        "sequence": int(component.get("SEQUENCE")),
                    }
                    # # In a VEVENT sometimes there are mutliple object ID with custom impacts
                    # circuits = component.get("X-MAINTNOTE-OBJECT-ID")
                    # if isinstance(circuits, list):
                    #     data["circuits"] = [
                    #         CircuitImpact(
                    #             circuit_id=str(object),
                    #             impact=Impact(
                    #                 object.params.get("X-MAINTNOTE-OBJECT-IMPACT", component.get("X-MAINTNOTE-IMPACT"))
                    #             ),
                    #         )
                    #         for object in component.get("X-MAINTNOTE-OBJECT-ID")
                    #     ]
                    # else:
                    #     data["circuits"] = [
                    #         CircuitImpact(circuit_id=circuits, impact=Impact(component.get("X-MAINTNOTE-IMPACT")),)
                    #     ]
                    result.append(data)

        except ValidationError as exc:
            raise MissingMandatoryFields from exc

        except Exception as exc:
            raise ParsingError from exc

        logger.debug("Successful parsing for %s", self.__class__.__name__)

        return result
