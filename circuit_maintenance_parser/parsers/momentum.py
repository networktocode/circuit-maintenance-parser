"""Momentum parser."""
import logging

from dateutil import parser

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class SubjectParserMomentum1(EmailSubjectParser):
    """Parser for Momentum subject string."""

    def parse_subject(self, subject):
        """Parse subject of email file.

        Example subject:
            [notices] Momentum Data Services | Planned Network Maintenance , | Customer Inc | | 11111111 | [ ref:11111.11111:ref ]
        """
        data = {}
        try:
            split = subject.split("|")
            if len(split) == 6:
                if "planned" in split[1].lower():
                    data["status"] = Status.CONFIRMED
                else:
                    data["status"] = Status.CONFIRMED
                data["maintenance_id"] = split[4].strip()
            else:
                raise ParserError("Unable to split subject correctly.")
            return [data]

        except Exception as exc:
            raise ParserError from exc


class HtmlParserMomentum1(Html):
    """Notifications Parser for Momentum notifications.

    <div>
        <p>
            <span><span><font>Account: Account Name</font></span></span>
        </p>
        <p>
            <span><span><font>Maintenance start date/time: 2021-08-14 09:30 AM UTC</font></span></span>
        </p>
        <p>
            <span><span><font>Maintenance finish date/time: 2021-08-14 11:30 AM UTC</font></span></span>
        </p>
    </div>
    """

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_body(soup.find_all("p"), data)
        return [data]

    def parse_body(self, p_elements, data):
        """Parse HTML body."""
        for element in p_elements:
            text = element.text.encode("ascii", errors="ignore").decode("utf-8")
            for line in text.splitlines():
                if "Account" in line:
                    data["account"] = line.split(": ")[1].strip()
                elif "Circuit ID" in line:
                    data["circuits"] = []
                    for circuit_id in line.split(": ")[1].split(", "):
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))
                elif "Maintenance start date/time" in line:
                    data["start"] = self.dt2ts(parser.parse(line.split("time:")[1]))
                elif "Maintenance finish date/time" in line:
                    data["end"] = self.dt2ts(parser.parse(line.split("time:")[1]))
                elif "Reason for Maintenance" in line:
                    data["summary"] = line.split(":")[1].strip()
