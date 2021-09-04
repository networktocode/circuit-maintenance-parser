"""Definition of Mainentance Notification base classes."""
import logging
import base64
import calendar
import datetime
import quopri
from typing import Iterable, Union, Dict, List
from email.utils import parsedate_tz, mktime_tz

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import BaseModel, Extra
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.output import Status, Impact, CircuitImpact

# pylint: disable=no-member

logger = logging.getLogger(__name__)


class Parser(BaseModel, extra=Extra.forbid):
    """Parser class.

    A Parser handles one or more specific data type(s) (specified in `data_types`).
    The `parse(raw)` method must be implemented to parse the `raw` data to extract the
    (possibly partial/incomplete) data that will eventually be used to create a Maintenance object.
    """

    # _data_types are used to match the Parser to to each type of DataPart
    _data_types = ["text/plain", "plain"]

    @classmethod
    def get_data_types(cls) -> List[str]:
        """Return the expected data type."""
        return cls._data_types

    def parse(self, raw: bytes) -> List[Dict]:
        """Extract a list of data that partially or completely describes a series of Maintenance objects."""
        raise NotImplementedError

    @staticmethod
    def dt2ts(date_time: datetime.datetime) -> int:
        """Converts a datetime object to UTC timestamp. Naive datetime will be considered UTC."""
        return calendar.timegm(date_time.utctimetuple())


class ICal(Parser):
    """Standard Notifications Parser based on ICal notifications.

    Reference: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
    """

    _data_types = ["text/calendar", "ical", "icalendar"]

    def parse(self, raw: bytes) -> List[Dict]:
        """Method that returns a list of Maintenance objects."""
        result = []

        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(raw))
        except ValueError:
            try:
                gcal = Calendar.from_ical(raw)
            except ValueError as exc:
                raise ParserError from exc

        if not gcal:
            raise ParserError("Not a valid iCalendar data received")

        try:
            gcal = Calendar.from_ical(raw)
            result = self.parse_ical(gcal)
        except Exception as exc:
            raise ParserError from exc

        logger.debug("Successful parsing for %s", self.__class__.__name__)

        return result

    @staticmethod
    def parse_ical(gcal: Calendar) -> List[Dict]:
        """Standard ICalendar parsing."""
        result = []
        for component in gcal.walk():
            if component.name == "VEVENT":
                data = {
                    "provider": str(component.get("X-MAINTNOTE-PROVIDER")),
                    "account": str(component.get("X-MAINTNOTE-ACCOUNT")),
                    "maintenance_id": str(component.get("X-MAINTNOTE-MAINTENANCE-ID")),
                    "status": Status(component.get("X-MAINTNOTE-STATUS")),
                    "start": round(component.get("DTSTART").dt.timestamp()),
                    "end": round(component.get("DTEND").dt.timestamp()),
                    "stamp": round(component.get("DTSTAMP").dt.timestamp()),
                    "summary": str(component.get("SUMMARY")),
                    "organizer": str(component.get("ORGANIZER")),
                    "uid": str(component.get("UID")),
                    "sequence": int(component.get("SEQUENCE")),
                }

                data = {key: value for key, value in data.items() if value != "None"}

                # In a VEVENT sometimes there are mutliple object ID with custom impacts
                circuits = component.get("X-MAINTNOTE-OBJECT-ID")
                if isinstance(circuits, list):
                    data["circuits"] = [
                        CircuitImpact(
                            circuit_id=str(object),
                            impact=Impact(
                                object.params.get("X-MAINTNOTE-OBJECT-IMPACT", component.get("X-MAINTNOTE-IMPACT"))
                            ),
                        )
                        for object in component.get("X-MAINTNOTE-OBJECT-ID")
                    ]
                else:
                    data["circuits"] = [
                        CircuitImpact(circuit_id=circuits, impact=Impact(component.get("X-MAINTNOTE-IMPACT")),)
                    ]
                result.append(data)
        return result


class Html(Parser):
    """Html parser."""

    _data_types = ["text/html", "html"]

    def parse(self, raw: bytes) -> List[Dict]:
        """Execute parsing."""
        result = []

        data_base: Dict[str, Union[int, str, Iterable]] = {}
        try:
            soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")

            # Even we have not noticed any HTML notification with more than one maintenance yet, we define the
            # return of `parse_html` as an Iterable object to accommodate this potential case.
            for data in self.parse_html(soup, data_base):
                result.append(data)

            logger.debug("Successful parsing for %s", self.__class__.__name__)

            return result

        except Exception as exc:
            raise ParserError from exc

    def parse_html(self, soup: ResultSet, data_base: Dict) -> List[Dict]:
        """Custom HTML parsing."""
        raise NotImplementedError

    @staticmethod
    def clean_line(line):
        """Clean up of undesired characters from Html."""
        try:
            line = line.text.strip()
        except AttributeError:
            line = line.strip()
        # TODO: below may not be needed if we use `quopri.decodestring()` on the initial email file?
        return line.replace("=C2", "").replace("=A0", "").replace("\r", "").replace("=", "").replace("\n", "")


class EmailDateParser(Parser):
    """Parser for Email Date."""

    _data_types = ["email-header-date"]

    def parse(self, raw: bytes) -> List[Dict]:
        """Method that returns a list of Maintenance objects."""
        try:
            result = [{"stamp": mktime_tz(parsedate_tz(raw.decode()))}]
            logger.debug("Successful parsing for %s", self.__class__.__name__)
            return result
        except Exception as exc:
            raise ParserError from exc
