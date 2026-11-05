"""Hawaiki parser."""

import logging
import re
from typing import Dict, List

from dateutil import parser

from circuit_maintenance_parser.output import CircuitImpact, Impact, Status
from circuit_maintenance_parser.parser import EmailSubjectParser, Text

logger = logging.getLogger(__name__)
IMPACT_LINE_RE = re.compile(r"^Service impact:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


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
            "account": "Customer info unavailable",
            "summary": "Hawaiki maintenance notification",
        }

        lines = text.splitlines()
        in_maintenance_window = False

        # All circuits in a Hawaiki notification share one "Service impact" line, and it appears
        # after the "Service ID" lines, so resolve it up front.
        impact = self._parse_impact(text)

        for line in lines:
            line = line.strip()

            match = re.match(r"Service ID:\s*(.+)", line)
            if match:
                circuit_id = match.group(1).strip()
                data["circuits"].append(CircuitImpact(circuit_id=circuit_id, impact=impact))
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

    @staticmethod
    def _parse_impact(text: str) -> Impact:
        """Map the notification's single 'Service impact' line to an Impact."""
        match = IMPACT_LINE_RE.search(text)
        if not match:
            logger.warning("No Hawaiki 'Service impact' line found, defaulting to OUTAGE.")
            return Impact.OUTAGE
        impact_text = match.group(1).strip().lower()
        if "no service impact" in impact_text:
            return Impact.NO_IMPACT
        if "redundancy" in impact_text or "re-routed" in impact_text:
            return Impact.REDUCED_REDUNDANCY
        logger.warning("Unrecognized Hawaiki service impact %r, defaulting to OUTAGE.", impact_text)
        return Impact.OUTAGE
