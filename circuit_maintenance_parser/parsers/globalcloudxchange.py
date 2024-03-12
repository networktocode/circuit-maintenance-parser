"""Circuit Maintenance Parser for Equinix Email Notifications."""

import re
from datetime import datetime
from typing import Any, Dict, List

from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Status


class HtmlParserGcx1(Html):
    """Custom Parser for HTML portion of Global Cloud Xchange circuit maintenance notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse an Global Cloud Xchange circuit maintenance email.

        Args:
            soup (ResultSet): beautiful soup object containing the html portion of an email.

        Returns:
            Dict: The data dict containing circuit maintenance data.
        """
        data: Dict[str, Any] = {"circuits": []}

        for div in soup.find_all("div"):
            for pstring in div.strings:
                search = re.search("Dear (.*),", pstring)
                if search:
                    data["account"] = search.group(1)

        # Find Circuits
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 2 and "Service ID" not in cols[0].text:
                    impact = "NO-IMPACT"
                    if cols[1].text == "At Risk":
                        impact = "REDUCED-REDUNDANCY"

                    data["circuits"].append({"circuit_id": cols[0].text, "impact": impact})

        return [data]


class SubjectParserGcx1(EmailSubjectParser):
    """Parse the subject of a Global Cloud Xchange circuit maintenance email. The subject contains the maintenance ID and status."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the Global Cloud Xchange Email subject for summary and status.

        Args:
            subject (str): subject of email
            e.g. 'PE2024020844407 | Emergency | Service Advisory Notice | Span Loss Rectification | 12-Feb-2024 09:00 (GMT) - 12-Feb-2024 17:00 (GMT)'.


        Returns:
            List[Dict]: Returns the data object with summary and status fields.
        """
        data = {}
        search = re.search(
            r"^([A-Z0-9]+) \| (\w+) \| ([\w\s]+) \| ([\w\s]+) \| (\d+-[A-Za-z]{3}-\d{4} \d{2}:\d{2}) \(GMT\) - (\d+-[A-Za-z]{3}-\d{4} \d{2}:\d{2}) \(GMT\)$",
            subject,
        )
        if search:
            data["maintenance_id"] = search.group(1)
            date_format = date_format = "%d-%b-%Y %H:%M"
            data["start"] = self.dt2ts(datetime.strptime(search.group(5), date_format))
            data["end"] = self.dt2ts(datetime.strptime(search.group(6), date_format))
            data["summary"] = search.group(4)

        if "completed" in subject.lower():
            data["status"] = Status.COMPLETED
        elif "rescheduled" in subject.lower():
            data["status"] = Status.RE_SCHEDULED
        elif "scheduled" in subject.lower() or "reminder" in subject.lower() or "notice" in subject.lower():
            data["status"] = Status.CONFIRMED
        elif "cancelled" in subject.lower():
            data["status"] = Status.CANCELLED
        else:
            # Some Global Cloud Xchange notifications don't clearly state a status in their subject.
            # From inspection of examples, it looks like "Confirmed" would be the most appropriate in this case.
            data["status"] = Status.CONFIRMED

        return [data]
