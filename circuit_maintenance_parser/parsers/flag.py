"""Circuit Maintenance Parser for FLAG Notifications.

Note: this is a fork of Globalcloudexchange parser.
"""

import re
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.output import Impact
from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Status


class HtmlParserFlag1(Html):
    """Custom Parser for HTML portion of FLAG circuit maintenance notifications."""

    def parse_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse an FLAG circuit maintenance email.

        Args:
            soup (BeautifulSoup): beautiful soup object containing the html portion of an email.

        Returns:
            Dict: The data dict containing circuit maintenance data.
        """
        data: Dict[str, Any] = {"circuits": []}
        self.parse_tables(soup.find_all("table", attrs={"border-collapse": "collapse"}), data)
        self.parse_paragraphs(soup.find_all("p"), data)

        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse table elements to find maintenance windows (start/end) and circuit ID's."""
        date_format = date_format = "%d-%b-%Y %H:%M"
        for table in tables:
            table_type = ""
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols[0].text.strip() == "Service ID":
                    table_type = "circuits"
                    continue
                if cols[0].text.strip() == "Window":
                    table_type = "windows"
                    continue

                # this table is listing all circuits
                if table_type == "circuits":
                    impact = Impact.OUTAGE
                    if "at risk" in cols[1].text.lower():
                        impact = Impact.REDUCED_REDUNDANCY

                    data["circuits"].append({"circuit_id": cols[0].text.strip(), "impact": impact})
                # this table is listing windows (note: for now, we will only use the last listed window)
                elif table_type == "windows":
                    data["start"] = self.dt2ts(datetime.strptime(cols[1].text.strip(), date_format))
                    data["end"] = self.dt2ts(datetime.strptime(cols[2].text.strip(), date_format))

    def parse_paragraphs(self, paragraphs: ResultSet, data: Dict):
        """Parse paragraph elements to find account and summary."""
        for p in paragraphs:
            for pstring in p.strings:
                # print(f"hoi: {pstring}")
                search = re.search("Dear (.*),", pstring)
                if search:
                    data["account"] = search.group(1).strip()
                    continue

                # after account has been set, next paragraph is the summary
                if "account" in data and "summary" not in data:
                    data["summary"] = pstring.strip()
                    continue


class SubjectParserFlag1(EmailSubjectParser):
    """Parse the subject of a FLAG circuit maintenance email. The subject contains the maintenance ID and status."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the FLAG Email subject for maintenance ID and status.

        Args:
            subject (str): subject of email
            e.g. 'FLAG | PE2025102750538 | Planned Event | Rescheduled'.


        Returns:
            List[Dict]: Returns the data object with maintenance_id and status fields.
        """
        data = {}
        search = re.search(
            r"^FLAG \| ([A-Z0-9]+) \| ([\w\s]+) \| ([\w\s]+)$",
            subject,
        )
        if search:
            data["maintenance_id"] = search.group(1)

        if "completed" in subject.lower():
            data["status"] = Status.COMPLETED
        elif "rescheduled" in subject.lower():
            data["status"] = Status.RE_SCHEDULED
        elif "scheduled" in subject.lower() or "reminder" in subject.lower() or "notice" in subject.lower():
            data["status"] = Status.CONFIRMED
        elif "cancelled" in subject.lower():
            data["status"] = Status.CANCELLED
        else:
            # Some FLAG notifications don't clearly state a status in their subject.
            # From inspection of examples, it looks like "Confirmed" would be the most appropriate in this case.
            data["status"] = Status.CONFIRMED

        return [data]
