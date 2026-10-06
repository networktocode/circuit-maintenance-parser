"""RETN parser."""

import logging
import re
from typing import Dict, List

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, Status

logger = logging.getLogger(__name__)


class HtmlParserRETN1(Html):
    """Notifications Parser for RETN notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Execute parsing."""
        data: Dict[str] = {"circuits": []}
        self.parse_bold(soup.find_all("b"), data)
        self.parse_h3(soup.find_all("h3"), data)
        self.parse_h4(soup.find_all("h4"), data)

        return [data]

    def parse_h3(self, headers: ResultSet, data: Dict):
        """Parse H3 elements to find the status."""
        for header in headers:
            if "Ticket Opened" in header.text:
                data["status"] = Status("CONFIRMED")
            elif "Ticket Resolved" in header.text:
                data["status"] = Status("COMPLETED")
            elif "New Update" in header.text:
                data["status"] = Status("IN-PROCESS")
            elif "Rescheduling Update" in header.text:
                data["status"] = Status("RE-SCHEDULED")

        if "status" not in data:
            data["status"] = Status("NO-CHANGE")

    def parse_h4(self, headers: ResultSet, data: Dict):
        """Parse H4 elements to find impact, CID's and summary."""
        for header in headers:
            # CID's will follow and impact inside of this element
            if "service" in header.text.lower():
                impact = Impact("NO-IMPACT")
                if "complete loss" in header.text:
                    impact = Impact("OUTAGE")
                elif "50 ms flaps" in header.text:
                    impact = Impact("REDUCED-REDUNDANCY")
                elif "services at risk" in header.text:
                    impact = Impact("REDUCED-REDUNDANCY")
                elif "RTT increasing" in header.text:
                    impact = Impact("REDUCED-REDUNDANCY")

                # Find CID's
                header_next = header.next_sibling
                while header_next:
                    text = header_next.text.strip()
                    if "description" in text.lower():
                        break

                    if header_next.text.strip() != "":
                        data["circuits"].append({"circuit_id": text, "impact": impact})

                    header_next = header_next.next_sibling

            # Summary will follow
            elif "Description" in header.text:
                data["summary"] = header.next_sibling.text.strip()

    def parse_bold(self, bolds: ResultSet, data: Dict):
        """Parse B (bold) elements to find start and end time."""
        for bold in bolds:
            if "planned start time" in bold.text.lower():
                data["start"] = self.dt2ts(parser.parse(bold.next_sibling.text.strip(), dayfirst=True))
            elif "planned end time" in bold.text.lower():
                data["end"] = self.dt2ts(parser.parse(bold.next_sibling.text.strip(), dayfirst=True))


class SubjectParserRETN1(EmailSubjectParser):
    """Parse the subject of an RETN circuit maintenance email. The subject contains the maintenance ID and account."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the RETN Email subject for maintenance ID and account.

        Example subject line: [RETN.NET Ticket#PW-40135152]: Planned Works Notification CID#133337

        """
        data = {}
        parse_subject = re.search(r"Ticket#([A-Z]+-[0-9]+)](.*)CID#([0-9]+)", subject)
        if parse_subject:
            data["maintenance_id"] = parse_subject[1]
            data["account"] = parse_subject[3]

        return [data]
