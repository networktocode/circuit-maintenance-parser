"""Definition of Mainentance Notification base classes."""
import logging
import os
import base64
import calendar
import datetime
import quopri
from typing import Dict, List
from email.utils import parsedate_tz, mktime_tz
import hashlib

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import BaseModel
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.output import Status, Impact, CircuitImpact
from circuit_maintenance_parser.constants import EMAIL_HEADER_SUBJECT, EMAIL_HEADER_DATE
from circuit_maintenance_parser.utils import Geolocator

# pylint: disable=no-member

logger = logging.getLogger(__name__)


class Parser(BaseModel):
    """Parser class.

    A Parser handles one or more specific data type(s) (specified in `data_types`).
    The `parse(raw)` method must be implemented to parse the `raw` data to extract the
    (possibly partial/incomplete) data that will eventually be used to create a Maintenance object.
    """

    # _data_types are used to match the Parser to to each type of DataPart
    _data_types = ["text/plain", "plain"]

    # TODO: move it to where it is used, Cogent parser
    _geolocator = Geolocator()

    @classmethod
    def get_data_types(cls) -> List[str]:
        """Return the expected data type."""
        return cls._data_types

    @classmethod
    def get_name(cls) -> str:
        """Return the parser name."""
        return cls.__name__

    def parser_hook(self, raw: bytes, content_type: str) -> List[Dict]:
        """Custom parser logic.

        This method is used by the main `Parser` classes (such as `ICal` or `Html` parser) to define a shared
        logic (prepare data to process or just define the logic to extract the data), and it will contain at some point
        a call to the specific method that will be overwritten for each final customization from a `Provider`.
        For instance, the `Html.parser_hook` method calls the `parse_html` method after initializing the
        `bs4.BeautifulSoup` and this is the method that each specific parser will implement to finally extract the
        desired data from the raw content.
        """
        raise NotImplementedError

    def parse(self, raw: bytes, content_type: str) -> List[Dict]:
        """Execute parsing.

        Do not override this method!
        Instead, each main `Parser` class should implement its own custom logic within the `parser_hook` method.
        """
        try:
            result = self.parser_hook(raw, content_type)
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

    def parser_hook(self, raw: bytes, content_type: str):
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
                    # status may be omitted, per the BCOP
                    "status": Status(component.get("X-MAINTNOTE-STATUS", "NO-CHANGE")),
                    "start": round(component.get("DTSTART").dt.timestamp()),
                    "end": round(component.get("DTEND").dt.timestamp()),
                    "stamp": round(component.get("DTSTAMP").dt.timestamp()),
                    "summary": str(component.get("SUMMARY")),
                    "organizer": str(component.get("ORGANIZER")),
                    "uid": str(component.get("UID")),
                    # per the BCOP sequence is mandatory, but we have real examples where it's omitted,
                    # usually in combination with an omitted status. In that case let's treat the sequence as -1,
                    # i.e. older than all known updates.
                    "sequence": int(component.get("SEQUENCE", -1)),
                }

                data = {key: value for key, value in data.items() if value != "None"}

                # In a VEVENT sometimes there are mutliple object ID with custom impacts
                # In addition, while circuits should always be populated according to the BCOP, sometimes
                # they are not in the real world, at least in maintenances with a CANCELLED status.  Thus
                # we allow empty circuit lists, but will validate elsewhere that they are only empty in a
                # maintenance object with a CANCELLED status.
                circuits = component.get("X-MAINTNOTE-OBJECT-ID", [])
                if isinstance(circuits, list):
                    data["circuits"] = [
                        CircuitImpact(
                            circuit_id=str(object),
                            impact=Impact(
                                object.params.get("X-MAINTNOTE-OBJECT-IMPACT", component.get("X-MAINTNOTE-IMPACT"))
                            ),
                        )
                        for object in component.get("X-MAINTNOTE-OBJECT-ID", [])
                    ]
                else:
                    data["circuits"] = [
                        CircuitImpact(
                            circuit_id=circuits,
                            impact=Impact(component.get("X-MAINTNOTE-IMPACT")),
                        )
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

    def parser_hook(self, raw: bytes, content_type: str):
        """Execute parsing."""
        result = []
        soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")
        # Even we have not noticed any HTML notification with more than one maintenance yet, we define the
        # return of `parse_html` as an Iterable object to accommodate this potential case.
        for data in self.parse_html(soup):
            result.append(data)

        return result

    def parse_html(
        self,
        soup: ResultSet,
    ) -> List[Dict]:
        """Custom HTML parsing."""
        raise NotImplementedError

    @staticmethod
    def clean_line(line):
        """Clean up of undesired characters from Html."""
        try:
            return line.text.strip()
        except AttributeError:
            return line.strip()


class EmailDateParser(Parser):
    """Parser for Email Date."""

    _data_types = [EMAIL_HEADER_DATE]

    def parser_hook(self, raw: bytes, content_type: str):
        """Execute parsing."""
        parsed_date = parsedate_tz(raw.decode())
        if parsed_date:
            return [{"stamp": mktime_tz(parsed_date)}]
        raise ParserError("Not parsed_date available.")


class EmailSubjectParser(Parser):
    """Parse data from subject or email."""

    _data_types = [EMAIL_HEADER_SUBJECT]

    def parser_hook(self, raw: bytes, content_type: str):
        """Execute parsing."""
        result = []
        for data in self.parse_subject(self.bytes_to_string(raw).replace("\r", "").replace("\n", "")):
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

    def parser_hook(self, raw: bytes, content_type: str):
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

    def parser_hook(self, raw: bytes, content_type: str):
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


class LLM(Parser):
    """LLM parser."""

    _data_types = ["text/html", "html", "text/plain"]

    _llm_question = """Please, could you extract a JSON form without any other comment,
    with the following JSON schema (timestamps in EPOCH and taking into account the GMT offset):
    {
    "type": "object",
    "properties": {
        "start": {
            "type": "int",
        },
        "end": {
            "type": "int",
        },
        "account": {
            "type": "string",
        },
        "summary": {
            "type": "string",
        },
        "maintenance_id": {
            "type": "string",
        },
        "account": {
            "type": "string",
        },
        "status": {
            "type": "string",
        },
        "impact": {
            "type": "string",
        },
        "circuit_ids": {
            "type": "array",
            "items": {
                "type": "string",
            }
        }
    }
    More context:
    * Circuit IDs are also known as service or order
    * Status could be confirmed, ongoing, cancelled, completed or rescheduled
    """

    def parser_hook(self, raw: bytes, content_type: str):
        """Execute parsing."""
        result = []
        if content_type in ["html", "text/html"]:
            soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")
            content = soup.text
        elif content_type in ["text/plain"]:
            content = self.get_text_hook(raw)

        for data in self.parse_content(content):
            result.append(data)
        return result

    @staticmethod
    def get_text_hook(raw: bytes) -> str:
        """Can be overwritten by subclasses."""
        return raw.decode()

    @staticmethod
    def get_key_with_string(dictionary: dict, string: str):
        """Returns the key in the dictionary that contains the given string."""
        for key in dictionary.keys():
            if string in key:
                return key
        return None

    @property
    def llm_question(self):
        """Return the LLM question."""
        custom_llm_question = os.getenv("PARSER_LLM_QUESTION_STR")
        if custom_llm_question:
            return custom_llm_question

        custom_llm_question_path = os.getenv("PARSER_LLM_QUESTION_FILEPATH")
        if custom_llm_question_path:
            try:
                with open(custom_llm_question_path, mode="r", encoding="utf-8") as llm_question_file:
                    return llm_question_file.read()
            except OSError as err:
                logger.warning("The file %s can't be read: %s", custom_llm_question_path, err)

        return self._llm_question

    def get_llm_response(self, content):
        """Method to retrieve the response from the LLM for some content."""
        raise NotImplementedError

    def _get_impact(self, generated_json: dict):
        """Method to get a general Impact for all Circuits."""
        impact_key = self.get_key_with_string(generated_json, "impact")
        if impact_key:
            if "no impact" in generated_json[impact_key].lower():
                return Impact.NO_IMPACT
            if "partial" in generated_json[impact_key].lower():
                return Impact.DEGRADED

        return Impact.OUTAGE

    def _get_circuit_ids(self, generated_json: dict, impact: Impact):
        """Method to get the Circuit IDs and use a general Impact."""
        circuits = []
        circuits_ids_key = self.get_key_with_string(generated_json, "circuit")
        for circuit in generated_json[circuits_ids_key]:
            if isinstance(circuit, str):
                circuits.append(CircuitImpact(circuit_id=circuit, impact=impact))
            elif isinstance(circuit, dict):
                circuit_key = self.get_key_with_string(circuit, "circuit")
                circuits.append(CircuitImpact(circuit_id=circuit[circuit_key], impact=impact))

        return circuits

    def _get_start(self, generated_json: dict):
        """Method to get the Start Time."""
        return generated_json[self.get_key_with_string(generated_json, "start")]

    def _get_end(self, generated_json: dict):
        """Method to get the End Time."""
        return generated_json[self.get_key_with_string(generated_json, "end")]

    def _get_summary(self, generated_json: dict):
        """Method to get the Summary."""
        return generated_json[self.get_key_with_string(generated_json, "summary")]

    def _get_status(self, generated_json: dict):
        """Method to get the Status."""
        status_key = self.get_key_with_string(generated_json, "status")

        if "confirmed" in generated_json[status_key].lower():
            return Status.CONFIRMED
        if "rescheduled" in generated_json[status_key].lower():
            return Status.RE_SCHEDULED
        if "cancelled" in generated_json[status_key].lower():
            return Status.CANCELLED
        if "ongoing" in generated_json[status_key].lower():
            return Status.IN_PROCESS
        if "completed" in generated_json[status_key].lower():
            return Status.COMPLETED

        return Status.CONFIRMED

    def _get_account(self, generated_json: dict):
        """Method to get the Account."""
        account = generated_json[self.get_key_with_string(generated_json, "account")]
        if not account:
            return "Not found"

        return account

    def _get_maintenance_id(self, generated_json: dict, start, end, circuits):
        """Method to get the Maintenance ID."""
        maintenance_key = self.get_key_with_string(generated_json, "maintenance")
        if maintenance_key and generated_json["maintenance_id"] != "N/A":
            return generated_json["maintenance_id"]

        maintenance_id = str(start) + str(end) + "".join(list(circuits))
        return hashlib.md5(maintenance_id.encode("utf-8")).hexdigest()  # nosec

    def parse_content(self, content):
        """Parse content via LLM."""
        generated_json = self.get_llm_response(content)
        if not generated_json:
            return []

        impact = self._get_impact(generated_json)

        data = {
            "circuits": self._get_circuit_ids(generated_json, impact),
            "start": int(self._get_start(generated_json)),
            "end": int(self._get_end(generated_json)),
            "summary": str(self._get_summary(generated_json)),
            "status": self._get_status(generated_json),
            "account": str(self._get_account(generated_json)),
        }

        data["maintenance_id"] = str(
            self._get_maintenance_id(
                generated_json,
                data["start"],
                data["end"],
                data["circuits"],
            )
        )

        return [data]
