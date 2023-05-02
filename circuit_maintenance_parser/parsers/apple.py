import email
import re

from typing import Dict, List

from circuit_maintenance_parser.output import Impact, Status
from circuit_maintenance_parser.parser import EmailSubjectParser, Text, CircuitImpact

class SubjectParserApple(EmailSubjectParser):
    def parse_subject(self, subject: str) -> List[Dict]:
        return [{'summary': subject}]


class TextParserApple(Text):
    def parse_text(self, text: str) -> List[Dict]:
        data = {
            'circuits': self._circuits(text),
            'maintenance_id': self._maintenance_id(text),
            'start': self._start_time(text),
            'stamp': self._start_time(text),
            'end': self._end_time(text),
            'status': Status.CONFIRMED, # Have yet to see anything but confirmation.
            'organizer': 'peering-noc@group.apple.com',
            'provider': 'apple',
            'account': 'Customer info unavailable'
        }
        return [data]

    def _circuits(self, text):
        pattern = r'Peer AS: (\d*)'
        m = re.search(pattern, text)
        return [CircuitImpact(
            circuit_id=f'AS{m.group(1)}',
            impact=Impact.OUTAGE)]

    def _maintenance_id(self, text):
        # Apple ticket numbers always starts with "CHG".
        pattern = r'CHG(\d*)'
        m = re.search(pattern, text)
        return m.group(0)

    def _get_time(self, pattern, text):
        # Apple sends timestamps as RFC2822, misused
        # email module to convert to datetime.
        m = re.search(pattern, text)
        rfc2822 = m.group(1)
        time_tuple = email.utils.parsedate_tz(rfc2822)
        return email.utils.mktime_tz(time_tuple)

    def _start_time(self, text):
        pattern = 'Start Time: ([a-zA-Z0-9 :]*)'
        return self._get_time(pattern, text)

    def _end_time(self, text):
        pattern = 'End Time: ([a-zA-Z0-9 :]*)'
        return self._get_time(pattern, text)
