"""Cogent parser."""
import logging
import re
from typing import Dict, List
from datetime import datetime
from pytz import timezone, UTC
from bs4.element import ResultSet  # type: ignore

from circuit_maintenance_parser.parser import CircuitImpact, EmailSubjectParser, Html, Impact, Status, Text

from pprint import pprint

logger = logging.getLogger(__name__)

# pylint: disable=too-many-branches

class SubjectParserCogent1(EmailSubjectParser):
    """Subject parser for Cogent nofifications."""

    def parse_subject(self, subject: str):
        """Parse subject.

        Example: 

        11/19/2022 Circuit Provider Maintenance - Edina, MN 1-300123456
        Correction 06/11/2021 AB987654321-1 Planned Network Maintenance - San Jose, CA 1-123456789
        """
        print(subject)
        data = {}
        if subject.startswith("Correction"):
            data["status"] = Status("RE-SCHEDULED")
        elif "Planned" in subject or "Maintenance" in subject:
            data["status"] = Status("CONFIRMED")
        else:
            data["status"] = Status("CONFIRMED")

        

class TextParserCogent1(Text):
    """Parse text body of Cogent emails"""

    def parse_text(self, text):
        """Execute parsing of text

        Example:
            CIRCUIT PROVIDER MAINTENANCE

            Dear Cogent Customer,

            As a valued customer, Cogent is committed to keeping you informed about any changes in the status of your service with us. This email is to alert you regarding a circuit provider maintenance which will affect your connection to Cogent:

            Start time: 10:00pm CT 11/19/2022
            End time: 5:00am CT 11/20/2022
            Work order number: VN16123
            Order ID(s) impacted: 1-300123456
            Expected Outage/Downtime: 7 hours

            Cogent customers receiving service in Edina, MN will be affected by this outage. This outage has been scheduled by Zayo. The purpose of this maintenance is to repair damaged fiber. Only the Cogent Order ID(s) above will be impacted.

            During this maintenance window, you will experience an interruption in service while Zayo completes the maintenance activities; the interruption is expected to be less than 7 hours; however, due to the complexity of the work, your downtime may be longer.

            Our network operations engineers closely monitor the work and will do everything possible to minimize any inconvenience to you.  If you have any problems with your connection after this time, or if you have any questions regarding the maintenance at any point, please call Customer Support at 1-877-7-COGENT and refer to this Maintenance Ticket: VN16123.
        
        """
        data = {
            "circuits": [],
            "summary": "",
        }

        lines = text.splitlines()

        for line in lines:
            print(f"LINE: {line}")
            if line.startswith("Dear"):
                match = re.search(r"Dear (.*),", line)
                if match:
                    data["account"] = match.group(1)
            elif line.startswith("Start time:"):
                match = re.search(r"Start time: ([A-Za-z\d: ]*) [()A-Za-z\s]+ (\d+/\d+/\d+)", line)
                if match:
                    start_str = " ".join(match.groups())
            elif line.startswith("End time:"):
                match = re.search(r"End time: ([A-Za-z\d: ]*) [()A-Za-z\s]+ (\d+/\d+/\d+)", line)
                if match:
                    end_str = " ".join(match.groups())
            elif line.startswith("Cogent customers receiving service"):
                data['summary'] = line
                print(f"LINE: {line}")
                match = re.search(r"[^Cogent].*?((\b[A-Z][a-z\s-]+)+, ([A-Za-z-]+[\s-]))", line)
                if match:
                    parsed_timezone = self._geolocator.city_timezone(match.group(1).strip())
                    local_timezone = timezone(parsed_timezone)
                    # set start time using the local city timezone
                    try:
                        start = datetime.strptime(start_str, "%I:%M %p %d/%m/%Y")
                    except:
                        start = datetime.strptime(start_str, "%I:%M%p %d/%m/%Y")
                    local_time = local_timezone.localize(start)
                    # set start time to UTC
                    utc_start = local_time.astimezone(UTC)
                    data["start"] = self.dt2ts(utc_start)
                    logger.info(
                        "Mapped start time %s at %s (%s), to %s (UTC)",
                        start_str,
                        match.group(1).strip(),
                        local_timezone,
                        utc_start,
                    )
                    # set end time using the local city timezone
                    try:
                        end = datetime.strptime(end_str, "%I:%M %p %d/%m/%Y")
                    except:
                        end = datetime.strptime(end_str, "%I:%M%p %d/%m/%Y")
                    local_time = local_timezone.localize(end)
                    # set end time to UTC
                    utc_end = local_time.astimezone(UTC)
                    data["end"] = self.dt2ts(utc_end)
                    logger.info(
                        "Mapped end time %s at %s (%s), to %s (UTC)",
                        end_str,
                        match.group(1).strip(),
                        local_timezone,
                        utc_end,
                    )
            elif line.startswith("Work order number:"):
                match = re.search("Work order number: (.*)", line)
                if match:
                    data["maintenance_id"] = match.group(1)
            elif line.startswith("Order ID(s) impacted:"):
                data["circuits"] = []
                match = re.search(r"Order ID\(s\) impacted: (.*)", line)
                if match:
                    for circuit_id in match.group(1).split(","):
                        data["circuits"].append(
                            CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.strip())
                        )
            elif line.startswith("During this maintenance"):
                summary = data["summary"]
                data["summary"] = summary + '\n' + line
        pprint(data)



class HtmlParserCogent1(Html):
    """Notifications Parser for Cogent notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_div(soup.find_all("div", class_="a3s aiL"), data)
        #self.parse_title(soup.find_all("title"), data)
        return [data]

    def parse_div(self, divs: ResultSet, data: Dict):  # pylint: disable=too-many-locals
        """Parse <div> tag."""
        start_str = ""
        end_str = ""

        for div in divs:
            for line in div.text.splitlines():
                if line.endswith("Network Maintenance"):
                    data["summary"] = line
                elif line.startswith("Dear"):
                    match = re.search(r"Dear (.*),", line)
                    if match:
                        data["account"] = match.group(1)
                elif line.startswith("Start time:"):
                    match = re.search(r"Start time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
                    if match:
                        start_str = " ".join(match.groups())
                elif line.startswith("End time:"):
                    match = re.search(r"End time: (.*) \([A-Za-z\s]+\) (\d+/\d+/\d+)", line)
                    if match:
                        end_str = " ".join(match.groups())
                elif line.startswith("Cogent customers receiving service"):
                    match = re.search(r"[^Cogent].*?((\b[A-Z][a-z\s-]+)+, ([A-Za-z-]+[\s-]))", line)
                    if match:
                        parsed_timezone = self._geolocator.city_timezone(match.group(1).strip())
                        local_timezone = timezone(parsed_timezone)
                        # set start time using the local city timezone
                        start = datetime.strptime(start_str, "%I:%M %p %d/%m/%Y")
                        local_time = local_timezone.localize(start)
                        # set start time to UTC
                        utc_start = local_time.astimezone(UTC)
                        data["start"] = self.dt2ts(utc_start)
                        logger.info(
                            "Mapped start time %s at %s (%s), to %s (UTC)",
                            start_str,
                            match.group(1).strip(),
                            local_timezone,
                            utc_start,
                        )
                        # set end time using the local city timezone
                        end = datetime.strptime(end_str, "%I:%M %p %d/%m/%Y")
                        local_time = local_timezone.localize(end)
                        # set end time to UTC
                        utc_end = local_time.astimezone(UTC)
                        data["end"] = self.dt2ts(utc_end)
                        logger.info(
                            "Mapped end time %s at %s (%s), to %s (UTC)",
                            end_str,
                            match.group(1).strip(),
                            local_timezone,
                            utc_end,
                        )
                elif line.startswith("Work order number:"):
                    match = re.search("Work order number: (.*)", line)
                    if match:
                        data["maintenance_id"] = match.group(1)
                elif line.startswith("Order ID(s) impacted:"):
                    data["circuits"] = []
                    match = re.search(r"Order ID\(s\) impacted: (.*)", line)
                    if match:
                        for circuit_id in match.group(1).split(","):
                            data["circuits"].append(
                                CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id.strip())
                            )
            break

    @staticmethod
    def parse_title(title_results: ResultSet, data: Dict):
        """Parse <title> tag."""
        for title in title_results:
            if title.text.startswith("Correction"):
                data["status"] = Status("RE-SCHEDULED")
            elif "Planned" in title.text:
                data["status"] = Status("CONFIRMED")
