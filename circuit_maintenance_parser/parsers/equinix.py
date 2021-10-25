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
            "circuits": [],
            "status": Status.CONFIRMED,
            # "impact": Impact.OUTAGE,
        }
        impact = self._parse_b(soup.find_all("b"),data)
        self._parse_table(soup.find_all("th"), data, impact)

        # data.pop("impact")
        return [data]

    def _parse_b(self, b_elements, data):
        """Parse the <b> elements from the notification to capture
        start and end times, description, and impact. 

        Args:
            b_elements (): resulting soup object with all <b> elements
            data (Dict): data from the circuit maintenance
        """
        for b in b_elements:
            if "UTC:" in b:
                raw_time = b.next_sibling
                if not raw_time.isascii():
                    continue
                start_end_time = raw_time.split('-')
                if len(start_end_time) == 2:
                    data['start'] = self.dt2ts(parser.parse(raw_time.split('-')[0].strip()))
                    data['end'] = self.dt2ts(parser.parse(raw_time.split('-')[1].strip()))
            # if "DESCRIPTION:" in b:
            #     print(b.next_sibling)
            #     data['summary'] = b.next_sibling
            if "IMPACT:" in b:
                impact_line = b.next_sibling
                if "No impact to your service" in impact_line:
                    impact = Impact.NO_IMPACT
                elif "There will be service interruptions" in impact_line.next_sibling.text:
                    impact = Impact.OUTAGE
                    
        print(data)
        return(impact)

    def _parse_table(self, theader_elements, data, impact):
        for th in theader_elements:
            if "Account #" in th:
                circuit_table = th.find_parent("table")
                for tr in circuit_table.find_all("tr"):
                    if tr.find(th):
                        continue
                    circuit_info = list(tr.find_all("td"))
                    if circuit_info:
                        account, product, circuit = circuit_info
                        data['circuits'].append({
                            'circuit_id': circuit.text,
                            'impact': impact,
                        })
                        data['account'] = account.text

                    
  
class SubjectParserEquinix(EmailSubjectParser):
    def parse_subject(self, subject: str) -> List[Dict]:
        # parse the subject
        # Subject: Scheduled software upgrade in metro connect platform-SG Metro Area
        # Network Maintenance -19-OCT-2021 [5-212760022356]
        data = {}
        maintenance_id = re.search(r'\[(.*)\]$', subject)
        if maintenance_id:
            data['maintenance_id'] = maintenance_id[1]
        data['summary'] = subject
        if "COMPLETED" in subject:
            data['status'] = Status.COMPLETED
        return [data]
    
