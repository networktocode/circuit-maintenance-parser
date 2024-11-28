"""Circuit maintenance parser for Tata Email notifications."""
from typing import List, Dict, Any
from datetime import datetime

from bs4.element import ResultSet
from circuit_maintenance_parser.output import Impact, Status
from circuit_maintenance_parser.parser import Html, EmailSubjectParser


class HtmlParserTata(Html):
    """Custom Parser for HTML portion of Tata circuit maintenance notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse Tata circuit maintenance email."""
        prev: str = ""
        data: Dict[str, Any] = {
            "account": "N/A",
            "circuits": [],
            "organizer": soup.select("a[href^=mailto]")[0].text.strip(),
        }
        for span in soup.find_all("span"):
            curr = span.text.strip()
            if curr != prev:
                if prev.lower() == "ticket reference - tcl":
                    data["maintenance_id"] = curr
                elif prev.lower() == "service id":
                    for circuit in curr.split(","):
                        data["circuits"].append(
                            {
                                "circuit_id": circuit.strip(),
                                "impact": Impact.OUTAGE,
                            }
                        )
                elif prev.lower() == "activity window (gmt)" or prev.lower() == "revised activity window (gmt)":
                    start_end = curr.split("to")
                    data["start"] = self._parse_time(start_end[0])
                    data["end"] = self._parse_time(start_end[1])
                elif "extended up to time window" in prev.lower():
                    if "gmt" in curr.lower():
                        data["end"] = self._parse_time(curr)
            prev = span.text.strip()

        return [data]

    @staticmethod
    def _parse_time(string: str) -> str:
        """Convert YYYY-MM-DD HH:MM:SS GMT to epoch."""
        return int((datetime.strptime(string.strip(), "%Y-%m-%d %H:%M:%S GMT") - datetime(1970, 1, 1)).total_seconds())


class SubjectParserTata(EmailSubjectParser):
    """Custom Parser for Email subject of Tata circuit maintenance notifications."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse Tata Email subject for summary and status."""
        data: Dict[str, Any] = {"summary": subject.strip().replace("\n", "")}
        if "completion" in subject.lower():
            data["status"] = Status.COMPLETED
        elif "reschedule" in subject.lower() or "extension" in subject.lower():
            data["status"] = Status.RE_SCHEDULED
        elif "reminder" in subject.lower():
            data["status"] = Status.CONFIRMED
        elif "cancellation" in subject.lower():
            data["status"] = Status.CANCELLED
        else:
            data["status"] = Status.CONFIRMED

        return [data]
