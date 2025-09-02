"""AWS parser."""

import hashlib
import logging
import quopri
import re

import bs4  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, EmailSubjectParser, Impact, Status, Text

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class SubjectParserAWS1(EmailSubjectParser):
    """Subject parser for AWS notifications."""

    def parse_subject(self, subject):
        """Parse subject.

        Example: AWS Direct Connect Planned Maintenance Notification [AWS Account: 00000001]
        """
        data = {}
        search = re.search(r"\[AWS Account ?I?D?: ([0-9]+)\]", subject)
        if search:
            data["account"] = search.group(1)
        return [data]


class TextParserAWS1(Text):
    """Parse text body of email."""

    @staticmethod
    def get_text_hook(raw):
        """Modify soup before entering `parse_text`."""
        soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")
        return soup.text

    def parse_text(self, text):
        """Parse text.

        Example:
            Hello,

            Planned maintenance has been scheduled on an AWS Direct Connect router in A=
            Block, New York, NY from Thu, 20 May 2021 08:00:00 GMT to Thu, 20 Ma=
            y 2021 14:00:00 GMT for 6 hours. During this maintenance window, your AWS D=
            irect Connect services listed below may become unavailable.

            aaaaa-00000001
            aaaaa-00000002
            aaaaa-00000003
            aaaaa-00000004
            aaaaa-00000005
            aaaaa-00000006

            This maintenance is scheduled to avoid disrupting redundant connections at =
            the same time.
        """
        data = {"circuits": []}
        impact = Impact.OUTAGE
        maintenance_id = ""
        status = Status.CONFIRMED
        if re.search(r'<!doctype html>', text, re.IGNORECASE):
            soup = bs4.BeautifulSoup(text, 'html.parser')
            clean_string = soup.get_text()
            clean_string = re.sub('=20', '', clean_string)
            clean_list = clean_string.splitlines()
            cleaner_list = []
            for line in clean_list:
                newline = line.strip()
                if newline != "":
                    cleaner_list.append(newline)
            sumstart = cleaner_list.index('Hello,')
            try:
                sumend = cleaner_list.index('[1] https://aws.amazon.com/support')
            except ValueError:
                sumend = len(cleaner_list)
            summary = ""
            for line in cleaner_list[sumstart:sumend]:
                summary+=f"{line}\n"
            if "may become unavailable" in summary.lower():
                impact = Impact.OUTAGE
            elif "has been cancelled" in summary.lower():
                status = Status.CANCELLED
            start_time = cleaner_list[cleaner_list.index('Start time')+1]
            end_time = cleaner_list[cleaner_list.index('End time')+1]
            data["start"] = self.dt2ts(parser.parse(start_time))
            data["end"] = self.dt2ts(parser.parse(end_time))
            data["summary"] = summary
            for line in summary.splitlines():
                line = line.strip()
                maintenance_id += line
                data["circuits"].append(CircuitImpact(circuit_id=line, impact=impact))
            maintenance_id += str(data["start"])
            maintenance_id += str(data["end"])
        else:
            for line in text.splitlines():
                if "planned maintenance" in line.lower() or "maintenance has been scheduled" in line.lower():
                    data["summary"] = line
                    search = re.search(
                        r"([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3}) to ([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3})",
                        line,
                    )
                    if search:
                        data["start"] = self.dt2ts(parser.parse(search.group(1)))
                        data["end"] = self.dt2ts(parser.parse(search.group(2)))
                        maintenance_id += str(data["start"])
                        maintenance_id += str(data["end"])
                    if "may become unavailable" in line.lower():
                        impact = Impact.OUTAGE
                    elif "has been cancelled" in line.lower():
                        status = Status.CANCELLED
                    maintenance_id += line
                    data["circuits"].append(CircuitImpact(circuit_id=line, impact=impact))
        # No maintenance ID found in emails, so a hash value is being generated using the start,
        #  end and IDs of all circuits in the notification.
        data["maintenance_id"] = hashlib.sha256(maintenance_id.encode("utf-8")).hexdigest()  # nosec
        data["status"] = status
        return [data]
