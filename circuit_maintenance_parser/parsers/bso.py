"""BSO parser."""

import logging
from typing import Dict

from dateutil import parser
from bs4.element import ResultSet, Tag  # type: ignore

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status


logger = logging.getLogger(__name__)


class HtmlParserBSO1(Html):
    """Notifications Parser for BSO maintenance notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse Table tag."""
        data["account"] = "Customer info unavailable"  # No Account Name information in html/email details
        for idx, table in enumerate(tables):
            tbody_elements = table.find_all("tbody")
            if idx == 4:
                td_title = table.find_all("td")[1]  # contains the header
                if "Maintenance Update_" in td_title.find("span").text.strip():
                    data["status"] = Status("RE-SCHEDULED")
                elif "Maintenance End_" in td_title.find("span").text.strip():
                    data["status"] = Status("COMPLETED")
                elif "Maintenance Canceled_" in td_title.find("span").text.strip():
                    data["status"] = Status("CANCELLED")
                elif "Maintenance Reminder_" in td_title.find("span").text.strip():
                    data["status"] = Status("CONFIRMED")
                else:
                    data["status"] = Status("CONFIRMED")
            if len(tbody_elements) == 1:
                td_elements = table.find_all("td")
                for td_element in td_elements:
                    self.parse_elements(idx, tables, td_element, data)

    def parse_elements(self, idx: int, tables: ResultSet, td_element: Tag, data: Dict):
        """Parse td elements."""
        if "Maintenance Reason" in td_element.text.strip():
            data["summary"] = tables[idx + 1].find("span").text.strip()
        if "Maintenance Details" in td_element.text.strip():
            span_elements = tables[idx + 2].find_all("span")
            for idz, span_element in enumerate(span_elements):
                if "Maintenance ID" in " ".join(span_element.text.strip().split()):
                    data["maintenance_id"] = span_elements[idz + 1].text.strip()
                # Some BSO maintenance notifications contain multiple timeslots
                # We will get the earliest as the start time and the latest as the end time
                elif "Timeslot start time" in " ".join(span_element.text.strip().split()):
                    start_ts = self.dt2ts(parser.parse(span_elements[idz + 1].text.strip()))
                    # Keep the earliest start time
                    if "start" not in data or data["start"] > start_ts:
                        data["start"] = start_ts
                elif "Timeslot end time" in " ".join(span_element.text.strip().split()):
                    end_ts = self.dt2ts(parser.parse(span_elements[idz + 1].text.strip()))
                    # Keep the latest end time
                    if "end" not in data or data["end"] < end_ts:
                        data["end"] = end_ts
                elif "Expected impact level" in " ".join(span_element.text.strip().split()):
                    self.parse_spans(idz, span_elements, data)

    @staticmethod
    def parse_spans(idz: int, span_elements: ResultSet, data: dict):
        """Parse spans."""
        data["circuits"] = []
        index = idz
        while index + 2 < len(span_elements):
            impact_level_text = span_elements[index + 2].text.strip()
            if "hard down" in impact_level_text.lower():
                impact_level = Impact("OUTAGE")
            elif "switch hit" in impact_level_text.lower():
                impact_level = Impact("REDUCED-REDUNDANCY")
            elif "at risk only" in impact_level_text.lower():
                impact_level = Impact("NO-IMPACT")
            else:
                impact_level = Impact("OUTAGE")
            data["circuits"].append(
                CircuitImpact(impact=impact_level, circuit_id=span_elements[index + 1].text.strip())
            )
            index += 2
