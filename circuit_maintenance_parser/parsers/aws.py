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
#logger.setLevel("DEBUG")


class SubjectParserAWS1(EmailSubjectParser):
    """Subject parser for AWS notifications."""

    def parse_subject(self, subject):
        """Parse subject.

        Example: AWS Direct Connect Planned Maintenance Notification [AWS Account: 00000001]
        """
        data = {"account": ""}
        # Common Subject strings for matching:
        subject_map = {
            "\[AWS Account ?I?D?: ([0-9]+)\]": "account",
        }

        regex_keys = re.compile("|".join(subject_map), re.IGNORECASE)

        # in case of a multi-line subject
        # match the subject map
        for line in subject.splitlines():
            line_matched = re.search(regex_keys, line)
            if not line_matched:
                continue
            for group_match in line_matched.groups():
                if group_match is not None:
                    for k, v in subject_map.items():
                        if re.search(k, line, re.IGNORECASE):
                            data[v] = group_match
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
        text_map = {
            "^Account ?I?D?: ([0-9]+)": "account",
            "^Start Time: ([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3})": "start",
            "^End Time: ([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3})": "end",
            "(?<=from )([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3}) to ([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3})": "start_and_end",
        }

        regex_keys = re.compile("|".join(text_map), re.IGNORECASE)

        data = {"circuits": [], "start": "", "end": ""}
        impact = Impact.OUTAGE
        maintenace_id = ""
        status = Status.CONFIRMED

        for line in text.splitlines():
            if "planned maintenance" in line.lower():
                data["summary"] = line
            # match against the regex strings
            line_matched = re.search(regex_keys, line)
            # if we have a string that's not in our text_map
            # there may still be some strings with data to capture.
            # otherwise, continue on.
            if not line_matched:
                if "may become unavailable" in line.lower():
                    impact = Impact.OUTAGE
                elif "has been cancelled" in line.lower():
                    status = Status.CANCELLED

                if re.match(r"[a-z]{5}-[a-z0-9]{8}", line):
                    maintenace_id += line
                    data["circuits"].append(CircuitImpact(circuit_id=line, impact=impact))
                continue

            # for lines that do match our regex strings.
            # grab the data and map the values to keys.
            for group_match in line_matched.groups():
                if group_match is not None:
                    for k, v in text_map.items():
                        if re.search(k, line_matched.string, re.IGNORECASE):
                            # Due to having a single line on some emails
                            # This causes multiple match groups
                            # However this needs to be split across keys.
                            # This could probably be cleaned up.
                            if v == "start_and_end" and data["start"] == "":
                                data["start"] = group_match
                            elif v == "start_and_end" and data["end"] == "":
                                data["end"] = group_match
                            else:
                                data[v] = group_match

        # Let's get our times in order.
        if data["start"] and data["end"]:
            data["start"] = self.dt2ts(parser.parse(data["start"]))
            data["end"] = self.dt2ts(parser.parse(data["end"]))
            maintenace_id += str(data["start"])
            maintenace_id += str(data["end"])

        # No maintenance ID found in emails, so a hash value is being generated using the start,
        #  end and IDs of all circuits in the notification.
        data["maintenance_id"] = hashlib.md5(maintenace_id.encode("utf-8")).hexdigest()  # nosec
        data["status"] = status
        return [data]
