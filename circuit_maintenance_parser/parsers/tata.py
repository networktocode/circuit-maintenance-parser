# pylint: disable=disallowed-name
"""Circuit maintenance parser for Tata Email notifications."""

from datetime import datetime
from typing import Any, Dict, List

from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.output import Impact, Status
from circuit_maintenance_parser.parser import EmailSubjectParser, Html


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
                prev_lower = prev.lower()
                if prev_lower == "ticket reference - tcl":
                    data["maintenance_id"] = curr
                elif prev_lower == "service id":
                    for circuit in curr.split(","):
                        data["circuits"].append(
                            {
                                "circuit_id": circuit.strip(),
                                "impact": Impact.OUTAGE,
                            }
                        )
                elif prev_lower in ("activity window (gmt)", "revised activity window (gmt)"):
                    start_end = curr.split("to")
                    data["start"] = self.dt2ts(datetime.strptime(start_end[0].strip(), "%Y-%m-%d %H:%M:%S %Z"))
                    data["end"] = self.dt2ts(datetime.strptime(start_end[1].strip(), "%Y-%m-%d %H:%M:%S %Z"))
                elif "extended up to time window" in prev_lower:
                    if "gmt" in curr.lower():
                        data["end"] = self.dt2ts(datetime.strptime(curr, "%Y-%m-%d %H:%M:%S %Z"))
            prev = span.text.strip()

        return [data]


class SubjectParserTata(EmailSubjectParser):
    """Custom Parser for Email subject of Tata circuit maintenance notifications."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse Tata Email subject for summary and status."""
        data: Dict[str, Any] = {"summary": subject.strip().replace("\n", "")}
        subject_lower = subject.lower()
        if "completion" in subject_lower:
            data["status"] = Status.COMPLETED
        elif "reschedule" in subject_lower or "extension" in subject_lower:
            data["status"] = Status.RE_SCHEDULED
        elif "reminder" in subject_lower:
            data["status"] = Status.CONFIRMED
        elif "cancellation" in subject_lower:
            data["status"] = Status.CANCELLED
        else:
            data["status"] = Status.CONFIRMED

        return [data]
