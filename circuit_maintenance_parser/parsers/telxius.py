"""Telxius parser."""

import logging
import re
from typing import Dict, List

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, Status

logger = logging.getLogger(__name__)


class HtmlParserTelxius1(Html):
    """Notifications Parser for Telxius notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Execute parsing."""
        data: Dict[str] = {"circuits": []}
        events: List = []
        self.parse_tables(soup.find_all("table"), data)
        self.parse_bold(soup.find_all("b"), data, events)

        # loop through all events created, as maintenance announcement can list multiple windows, but with the same impact/CIDs/etc.
        return_data = []
        i = 1
        for event in events:
            data_add = data.copy()
            data_add["start"] = event["start"]
            data_add["end"] = event["end"]
            # add a sequence number to the maintenance_id to keep the events with unique ID's
            if i > 1:
                data_add["maintenance_id"] = f"{data['maintenance_id']}-{i}"
            return_data.append(data_add)
            i += 1

        return return_data

    def parse_bold(self, bolds: ResultSet, data: Dict, events: List):
        """Parse B (bold) elements to find maintenance_id, summary and dates-list."""
        for bold in bolds:
            if "notification number" in bold.text.lower():
                data["maintenance_id"] = bold.next_sibling.text.strip()
            elif "description" in bold.text.lower():
                data["summary"] = bold.next_sibling.text.strip()
            elif "schedule" in bold.text.lower():
                # look for the list after the schedule-label was mentioned
                ul = bold.find_next("ul")
                self.parse_list_dates(ul.find_all("li"), events)

    def parse_list_dates(self, items: ResultSet, events: List):
        """Parse list elements to start and end datetime(s)."""
        for item in items:
            text = item.get_text(strip=True)
            # Remove optional notes like "(Backup Window)"
            text = text.split("(")[0].strip()
            if "Start Time" in text:
                start_str = text.split(": ")
                start = self.dt2ts(parser.parse(start_str[1]))
            elif "EndTime" in text and start:
                end_str = text.split(": ")
                end = self.dt2ts(parser.parse(end_str[1]))
                events.append({"start": start, "end": end})
            else:
                start_str, end_str = text.split(" - ")
                events.append({"start": self.dt2ts(parser.parse(start_str)), "end": self.dt2ts(parser.parse(end_str))})

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse table element to find circuit ID's."""
        for table in tables:
            crt_col = -1
            col = 0
            for thead in table.find_all("thead"):
                for tr_elem in thead.find_all("tr"):
                    for th_elem in tr_elem.find_all("th"):
                        # find which column number has CRT label (CID)
                        if th_elem.text == "CRT":
                            crt_col = col
                        col += 1

            # This table doesn't have a column with CRT label, continue to next table
            if crt_col == -1:
                continue

            for tbody in table.find_all("tbody"):
                for tr_elem in tbody.find_all("tr"):
                    col = 0
                    for td_elem in tr_elem.find_all("td"):
                        if col == crt_col:
                            data["circuits"].append({"circuit_id": td_elem.text.strip(), "impact": Impact("OUTAGE")})
                        col += 1


class SubjectParserTelxius1(EmailSubjectParser):
    """Parse the subject of an Telxius circuit maintenance email. The subject contains the maintenance ID, account and status."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the Telxius Email subject for maintenance ID, account and status."""
        data = {}
        parse_subject = re.search(
            r"(?:\[([A-Z]+)\]\s*)?(?:EMERGENCY )?(?:SCHEDULED )?Maintenance Notification: ([A-Z0-9]+) - (.*)",
            subject,
        )
        if parse_subject:
            data["maintenance_id"] = parse_subject[2]
            data["account"] = parse_subject[3]

            if parse_subject[1] == "UPDATE":
                data["status"] = Status("RE-SCHEDULED")
            elif parse_subject[1] == "START":
                data["status"] = Status("IN-PROCESS")
            elif parse_subject[1] == "COMPLETED":
                data["status"] = Status("COMPLETED")
            elif parse_subject[1] == "CANCELLED":
                data["status"] = Status("CANCELLED")
            else:
                data["status"] = Status("CONFIRMED")

        return [data]
