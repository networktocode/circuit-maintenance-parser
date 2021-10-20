"""Circuit Maintenance Parser for Equinix Email Notifications."""
import bs4
from typing import List, Dict
from bs4.element import ResultSet
from dateutil import parser
import re
from circuit_maintenance_parser.output import Impact
from circuit_maintenance_parser.parser import Html, EmailSubjectParser, Status


class HtmlParserEquinix(Html):
    def parse_html(self, soup:ResultSet) -> Dict:
        # Parse the Body of the Email that is HTML
        data = {
            "account": "TBD",
            "circuits": [{"circuit_id": "ID0001", "impact": Impact.NO_IMPACT}],
            "status": Status.CONFIRMED,
        }
        self._parse_b(soup.find_all("b"),data)

        data.pop('impact')
        return [data]

    def _parse_b(self, b_elements, data):
        
        for b in b_elements:
            if "UTC:" in b:
                raw_time = b.next_sibling
                print(raw_time)
                data['start'] = self.dt2ts(parser.parse(raw_time.split('-')[0].strip()))
                data['end'] = self.dt2ts(parser.parse(raw_time.split('-')[1].strip()))
            if "DESCRIPTION:" in b:
                print(b.next_sibling)
                data['summary'] = b.next_sibling
            if "IMPACT:" in b:
                impact = b.next_sibling
                if "No impact to your service" in impact:
                    data['impact'] = Impact.NO_IMPACT
                    

                
        




    
class SubjectParserEquinix(EmailSubjectParser):
    
    def parse_subject(self, subject: str) -> List[Dict]:
        # parse the subject
        # Subject: Scheduled software upgrade in metro connect platform-SG Metro Area
        # Network Maintenance -19-OCT-2021 [5-212760022356]
        data = {}
        maintenance_id = re.search(r'\[(.*)\]$', subject)
        if maintenance_id:
            data['maintenance_id'] = maintenance_id[1]
        return [data]
    
