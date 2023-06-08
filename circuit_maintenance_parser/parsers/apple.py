"""Apple peering parser."""
import email
import re

from datetime import datetime, timezone
from typing import Dict, List

from circuit_maintenance_parser.output import Impact, Status
from circuit_maintenance_parser.parser import EmailSubjectParser, Text, CircuitImpact


class SubjectParserApple(EmailSubjectParser):
    """Subject parser for Apple notification."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Use the subject of the email as summary.

        Args:
            subject (str): Message subjects

        Returns:
            List[Dict]: List of attributes for Maintenance object
        """
        return [{"summary": subject}]


class TextParserApple(Text):
    """Parse the plaintext content of an Apple notification.

    Args:
        Text (str): Plaintext message
    """

    def parse_text(self, text: str) -> List[Dict]:
        """Extract attributes from an Apple notification email.

        Args:
            text (str): plaintext message

        Returns:
            List[Dict]: List of attributes for Maintenance object
        """
        data = {
            "circuits": self._circuits(text),
            "maintenance_id": self._maintenance_id(text),
            "start": self._start_time(text),
            "stamp": self._start_time(text),
            "end": self._end_time(text),
            "status": Status.CONFIRMED,  # Have yet to see anything but confirmation.
            "organizer": "peering-noc@group.apple.com",
            "provider": "apple",
            "account": "Customer info unavailable",
        }
        return [data]

    def _circuits(self, text):  # pylint: disable=no-self-use
        pattern = r"Peer AS: (\d*)"
        match = re.search(pattern, text)
        return [CircuitImpact(circuit_id=f"AS{match.group(1)}", impact=Impact.OUTAGE)]

    def _maintenance_id(self, text):  # pylint: disable=no-self-use
        # Apple ticket numbers always starts with "CHG".
        pattern = r"CHG(\d*)"
        match = re.search(pattern, text)
        return match.group(0)

    def _get_time(self, pattern, text):  # pylint: disable=no-self-use
        # Apple sends timestamps as RFC2822 for the US
        # but a custom format for EU datacenters.
        match = re.search(pattern, text)
        try:
            # Try EU timestamp
            return int(
                datetime.strptime(match.group(1), "%Y-%m-%d(%a) %H:%M %Z").replace(tzinfo=timezone.utc).timestamp()
            )
        except ValueError:
            # Try RFC2822 - US timestamp
            rfc2822 = match.group(1)
            time_tuple = email.utils.parsedate_tz(rfc2822)
            return email.utils.mktime_tz(time_tuple)

    def _start_time(self, text):
        pattern = "Start Time: ([a-zA-Z0-9 :()-]*)"
        return self._get_time(pattern, text)

    def _end_time(self, text):
        pattern = "End Time: ([a-zA-Z0-9 :()-]*)"
        return self._get_time(pattern, text)
