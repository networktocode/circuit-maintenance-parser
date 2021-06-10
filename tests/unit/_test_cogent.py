"""Tests generic for parser."""
from tests.unit.conftest import maintenance_data
from circuit_maintenance_parser.parsers.cogent import ParserCogent
import json
import os
from pathlib import Path

import pytest
import quopri

from circuit_maintenance_parser.parsers.cogent import ParserCogent

import bs4
import re
from datetime import datetime

dir_path = os.path.dirname("/Users/pk/ntc/circuit-maintenance-parser/tests/integration/")


# @pytest.mark.parametrize(
#     "parser_class, raw_file, results_file",
#     [
#         (
#             ParserCogent,
#             Path(dir_path, "data", "cogent", "cogent1.html"),
#             Path(dir_path, "data", "cogent", "cogent1_result.json"),
#         ),
#     ],
# )
# def test_complete_parsing(parser_class, raw_file, results_file):
#     """Tests various parser."""
#     with open(raw_file, "rb") as file_obj:
#         parser = parser_class(raw=file_obj.read())

#     # parsed_notifications = parser.process()[0]
#     parsed_notifications = parser.parse_html

#     with open(results_file) as res_file:
#         expected_result = json.load(res_file)

#     assert json.loads(parsed_notifications.to_json()) == expected_result


def run():
    with open("/Users/pk/ntc/circuit-maintenance-parser-ntc/tests/integration/data/cogent/cogent1.html", "rb") as fp:
        data = {}
        # print(quopri.decodestring(fp.read()))
        soup = bs4.BeautifulSoup(quopri.decodestring(fp.read()), features="lxml")
        # soup = bs4.BeautifulSoup(fp.read(), features="lxml")
        print(soup)
        br_results = soup.find_all("br")
        for br in br_results:
            div_text = br.parent.text
            for line in re.split(r"\n", div_text):
                if line.endswith("Network Maintenance"):
                    if "Planned" in line:
                        data["status"] = "CONFIRMED"
                    else:
                        data["status"] = "TENTATIVE"
                    data["summary"] = line
                elif line.startswith("Dear"):
                    match = re.search("Dear (.*),", line)
                    if match:
                        data["account"] = match.group(1)
                    else:
                        data["account"] = "Cogent Customer"
                elif line.startswith("Start time:"):
                    match = re.search("Start time: (.*) \(local time\) (\d+/\d+/\d+)", line)
                    if match:
                        start = " ".join(match.groups())
                    data["start"] = datetime.strptime(start, "%I:%M %p %d/%m/%Y")
                elif line.startswith("End time:"):
                    match = re.search("End time: (.*) \(local time\) (\d+/\d+/\d+)", line)
                    if match:
                        end = " ".join(match.groups())
                    data["end"] = datetime.strptime(end, "%I:%M %p %d/%m/%Y")
                elif line.startswith("Work order number:"):
                    match = re.search("Work order number: (.*)", line)
                    if match:
                        data["maintenance_id"] = match.group(1)
                elif line.startswith("Order ID(s) impacted:"):
                    data["circuits"] = []
                    match = re.search("Order ID\(s\) impacted: (.*)$", line)
                    if match:
                        print(f"{match.group(1)}")
                        data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=match.group(1)))
                    else:
                        print(f"{match}")
            print(data)
            break


if __name__ == "__main__":
    run()
