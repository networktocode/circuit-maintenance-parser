"""Zayo parser."""
import datetime
from typing import Iterable
import bs4
import dateutil.parser as parser
from pydantic import ValidationError

from circuitmaint_parser.errors import ParsingError, MissingMandatoryFields
from circuitmaint_parser.parser import Html, Impact, CircuitImpact, Maintenance, Status

# pylint: disable=too-many-nested-blocks,no-member, too-many-branches


class ParserZayo(Html):
    """Notifications Parser for Zayo notifications."""

    provider_type: str = "zayo"

    # Default values for Zayo notifications
    _default_provider = "zayo"
    _default_organizer = "mr@zayo.com"

    def process(self) -> Iterable[Maintenance]:
        """Execute parsing."""
        data = {
            "provider": self._default_provider,
            "organizer": self._default_organizer,
        }
        try:
            soup = bs4.BeautifulSoup(self.raw, features="lxml")
            for line in soup.find_all("b"):
                if isinstance(line, bs4.element.Tag):
                    if line.text.lower().strip().startswith("maintenance ticket #:"):
                        data["maintenance_id"] = self.clean_line(line.next_sibling)
                    elif line.text.lower().strip().startswith("urgency:"):
                        urgency = self.clean_line(line.next_sibling)
                        if urgency == "Planned":
                            data["status"] = Status("CONFIRMED")
                    elif "activity date" in line.text.lower():
                        for sibling in line.next_siblings:
                            if "( GMT )" in sibling.text:
                                window = self.clean_line(sibling).strip("( GMT )").split(" to ")
                                start = parser.parse(window.pop(0))
                                data["start"] = int(datetime.datetime.timestamp(start))
                                end = parser.parse(window.pop(0))
                                data["end"] = int(datetime.datetime.timestamp(end))
                                break
                    elif line.text.lower().strip().startswith("reason for maintenance:"):
                        data["summary"] = self.clean_line(line.next_sibling)
                    elif line.text.lower().strip().startswith("date notice sent:"):
                        stamp = start = parser.parse(self.clean_line(line.next_sibling))
                        data["stamp"] = int(datetime.datetime.timestamp(stamp))
                    elif line.text.lower().strip().startswith("customer:"):
                        data["account"] = self.clean_line(line.next_sibling)

            data["circuits"] = self.process_circuit_table(soup)

            return [Maintenance(**data)]

        except ValidationError as exc:
            raise MissingMandatoryFields from exc

        except Exception as exc:
            raise ParsingError from exc

    def process_circuit_table(self, soup: bs4.BeautifulSoup) -> Iterable[CircuitImpact]:
        """Handles the circuit tables and returns a list of Circuit Impacts."""
        circuits = []
        tables = soup.find("table")
        for table in tables:
            head_row = table.findAll("th")
            if (
                self.clean_line(head_row[0]) != "Circuit Id"
                or self.clean_line(head_row[1]) != "Expected Impact"
                or self.clean_line(head_row[2]) != "A Location CLLI"
                or self.clean_line(head_row[3]) != "Z Location CLLI"
                or self.clean_line(head_row[4]) != "Legacy Circuit Id"
            ):
                raise AssertionError("Table headers are not correct")

            data_rows = table.findAll("td")
            if len(data_rows) % 5 != 0:
                raise AssertionError("Table format is not correct")
            number_of_circuits = int(len(data_rows) / 5)
            for idx in range(number_of_circuits):
                data_circuit = {}
                data_circuit["circuit_id"] = self.clean_line(data_rows[0 + idx])
                impact = self.clean_line(data_rows[1 + idx])
                if "hard down" in impact.lower():
                    data_circuit["impact"] = Impact("OUTAGE")
                    circuits.append(CircuitImpact(**data_circuit))
        return circuits
