"""Circuit maintenance parser for PCCW Email notifications."""
import re
from typing import List, Dict, Tuple, Any, ClassVar
from datetime import datetime

from bs4.element import ResultSet  # type: ignore
from circuit_maintenance_parser.output import Status
from circuit_maintenance_parser.parser import Html, EmailSubjectParser


class HtmlParserPCCW(Html):
    """Custom Parser for HTML portion of PCCW circuit maintenance notifications."""

    DATE_TIME_FORMAT: ClassVar[str] = "%d/%m/%Y %H:%M:%S"
    PROVIDER: ClassVar[str] = "PCCW Global"

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse PCCW circuit maintenance email.

        Args:
            soup: BeautifulSoup ResultSet containing the email HTML content

        Returns:
            List containing a dictionary with parsed maintenance data
        """
        data: Dict[str, Any] = {
            "circuits": [],
            "provider": self.PROVIDER,
            "account": self._extract_account(soup),
        }
        start_time, end_time = self._extract_maintenance_window(soup)
        data["start"] = self.dt2ts(start_time)
        data["end"] = self.dt2ts(end_time)

        return [data]

    def _extract_account(self, soup: ResultSet) -> str:
        """Extract customer account from soup."""
        customer_field = soup.find(string=re.compile("Customer Name :", re.IGNORECASE))
        return customer_field.split(":")[1].strip()

    def _extract_maintenance_window(self, soup: ResultSet) -> Tuple[datetime, datetime]:
        """Extract start and end times from maintenance window."""
        datetime_field = soup.find(string=re.compile("Date Time :", re.IGNORECASE))
        time_parts = (
            datetime_field.lower().replace("date time :", "-").replace("to", "-").replace("gmt", "-").split("-")
        )
        start_time = datetime.strptime(time_parts[1].strip(), self.DATE_TIME_FORMAT)
        end_time = datetime.strptime(time_parts[2].strip(), self.DATE_TIME_FORMAT)
        return start_time, end_time


class SubjectParserPCCW(EmailSubjectParser):
    """Custom Parser for Email subject of PCCW circuit maintenance notifications.

    This parser extracts maintenance ID, status and summary from the email subject line.
    """

    # Only completion notification doesn't come with ICal. Other such as planned outage, urgent maintenance,
    # amendment and cacellation notifications come with ICal. Hence, maintenance status is set to COMPLETED.
    DEFAULT_STATUS: ClassVar[Status] = Status.COMPLETED

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse PCCW circuit maintenance email subject.

        Args:
            subject: Email subject string to parse

        Returns:
            List containing a dictionary with parsed subject data including:
                - maintenance_id: Extracted from end of subject
                - status: Default COMPLETED status
                - summary: Cleaned subject line
        """
        data: Dict[str, Any] = {
            "maintenance_id": self._extract_maintenance_id(subject),
            "status": self.DEFAULT_STATUS,
            "summary": self._clean_summary(subject),
        }

        return [data]

    def _extract_maintenance_id(self, subject: str) -> str:
        """Extract maintenance ID from the end of subject line."""
        return subject.split("-")[-1].strip()

    def _clean_summary(self, subject: str) -> str:
        """Clean and format the summary text."""
        return subject.strip().replace("\n", "")
