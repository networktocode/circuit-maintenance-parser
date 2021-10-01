"""Definition of Mainentance Notification base classes."""
import logging
import base64
import calendar
import datetime
import quopri
from typing import Dict, List
from email.utils import parsedate_tz, mktime_tz

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import BaseModel, Extra
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.output import Status, Impact, CircuitImpact
from circuit_maintenance_parser.constants import EMAIL_HEADER_SUBJECT, EMAIL_HEADER_DATE

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

    def parser_hook(self, raw: bytes) -> List[Dict]:
        """Custom parser logic.

        This method is used by the main `Parser` classes (such as `ICal` or `Html` parser) to define a shared
        logic (prepare data to process or just define the logic to extract the data), and it will contain at some point
        a call to the specific method that will be overwritten for each final customization from a `Provider`.
        For instance, the `Html.parser_hook` method calls the `parse_html` method after initializing the
        `bs4.BeautifulSoup` and this is the method that each specific parser will implement to finally extract the
        desired data from the raw content.
        """
        raise NotImplementedError

    def parse(self, raw: bytes) -> List[Dict]:
        """Execute parsing.

        Do not override this method!
        Instead, each main `Parser` class should implement its own custom logic within the `parser_hook` method.
        """
        try:
            result = self.parser_hook(raw)
        except Exception as exc:
            raise ParserError from exc
        if any(not partial_result for partial_result in result):
            raise ParserError(
                f"{self.__class__.__name__} parser was not able to extract the expected data for each maintenance.\n"  # type: ignore
                f"  - Raw content: {raw}\n"  # type: ignore
                f"  - Result: {result}"
            )
        logger.debug("Successful parsing for %s", self.__class__.__name__)
        return result

    @staticmethod
    def dt2ts(date_time: datetime.datetime) -> int:
        """Converts a datetime object to UTC timestamp. Naive datetime will be considered UTC."""
        return calendar.timegm(date_time.utctimetuple())


class ICal(Parser):
    """Standard Notifications Parser based on ICal notifications.

    Reference: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
    """

    _data_types = ["text/calendar", "ical", "icalendar"]

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(raw))
        except ValueError:
            gcal = Calendar.from_ical(raw)

        if not gcal:
            raise ParserError("Not a valid iCalendar data received")

        return self.parse_ical(gcal)

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

    @staticmethod
    def remove_hex_characters(string):
        """Convert any hex characters to standard ascii."""
        return string.encode("ascii", errors="ignore").decode("utf-8")

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        result = []
        soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")
        # Even we have not noticed any HTML notification with more than one maintenance yet, we define the
        # return of `parse_html` as an Iterable object to accommodate this potential case.
        for data in self.parse_html(soup):
            result.append(data)

        return result

    def parse_html(self, soup: ResultSet,) -> List[Dict]:
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

    _data_types = [EMAIL_HEADER_DATE]

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        parsed_date = parsedate_tz(raw.decode())
        if parsed_date:
            return [{"stamp": mktime_tz(parsed_date)}]
        raise ParserError("Not parsed_date available.")


class EmailSubjectParser(Parser):
    """Parse data from subject or email."""

    _data_types = [EMAIL_HEADER_SUBJECT]

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        result = []
        for data in self.parse_subject(self.bytes_to_string(raw)):
            result.append(data)
        return result

    def parse_subject(self, subject: str) -> List[Dict]:
        """Custom subject parsing."""
        raise NotImplementedError

    @staticmethod
    def bytes_to_string(string):
        """Convert bytes variable to a string."""
        return string.decode("utf-8")


class Csv(Parser):
    """Csv parser."""

    _data_types = ["application/csv", "text/csv", "application/octet-stream"]

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        result = []
        for data in self.parse_csv(raw):
            result.append(data)

        return result

    @staticmethod
    def parse_csv(raw: bytes) -> List[Dict]:
        """Custom CSV parsing."""
        raise NotImplementedError


class Text(Parser):
    """Text parser."""

    _data_types = ["text/plain"]

    def parser_hook(self, raw: bytes):
        """Execute parsing."""
        result = []
        text = self.get_text_hook(raw)
        for data in self.parse_text(text):
            result.append(data)
        return result

    @staticmethod
    def get_text_hook(raw: bytes) -> str:
        """Can be overwritten by subclasses."""
        return raw.decode()

    def parse_text(self, text) -> List[Dict]:
        """Custom text parsing."""
        raise NotImplementedError
