"""Hawaiki parser."""

import logging
import re
from typing import Dict, List

from dateutil import parser

from circuit_maintenance_parser.output import CircuitImpact, Impact, Status
from circuit_maintenance_parser.parser import EmailSubjectParser, Text

logger = logging.getLogger(__name__)


class SubjectParserHawaiki1(EmailSubjectParser):
    """Extract maintenance_id from Hawaiki email subject."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Extract ticket number from subject like '[Ticket#2026072290001004] ...'."""
        match = re.search(r"\[Ticket#(\S+)\]", subject)
        if match:
            return [{"maintenance_id": match.group(1)}]
        return [{}]


class TextParserHawaiki1(Text):
    """Parse plain-text body of Hawaiki initial maintenance notifications."""

    def parse_text(self, text: str) -> List[Dict]:
        """Extract attributes from Hawaiki notification.

        Example:
            Service ID: HW-CID-12345

            Maintenance Window
            Start: 2026-August-05 20:00 UTC
            End: 2026-August-05 21:00 UTC
        """
        data: Dict = {
            "circuits": [],
            "status": Status.CONFIRMED,
            "account": "Unknown",
            "summary": "Hawaiki maintenance notification",
        }

        lines = text.splitlines()
        in_maintenance_window = False

        for line in lines:
            line = line.strip()

            match = re.match(r"Service ID:\s*(.+)", line)
            if match:
                circuit_id = match.group(1).strip()
                data["circuits"].append(CircuitImpact(circuit_id=circuit_id, impact=Impact.NO_IMPACT))
                continue

            if line == "Maintenance Window":
                in_maintenance_window = True
                continue

            if in_maintenance_window:
                match = re.match(r"Start:\s*(.+)", line)
                if match:
                    data["start"] = self.dt2ts(parser.parse(match.group(1).strip()))
                    continue
                match = re.match(r"End:\s*(.+)", line)
                if match:
                    data["end"] = self.dt2ts(parser.parse(match.group(1).strip()))
                    in_maintenance_window = False
                    continue

        return [data]
