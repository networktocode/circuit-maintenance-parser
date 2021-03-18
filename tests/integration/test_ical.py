"""Tests for Ical parser."""
import json
import os
from pathlib import Path

import pytest

from circuitmaint_parser.parser import ICal
from circuitmaint_parser.errors import MissingMandatoryFields, ParsingError


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "raw_file, results_file",
    [
        (Path(dir_path, "data", "ical", "ical1"), Path(dir_path, "data", "ical", "ical1_result.json"),),
        (Path(dir_path, "data", "ical", "ical2"), Path(dir_path, "data", "ical", "ical2_result.json"),),
        (Path(dir_path, "data", "ical", "ical3"), Path(dir_path, "data", "ical", "ical3_result.json"),),
        (Path(dir_path, "data", "ical", "ical4"), Path(dir_path, "data", "ical", "ical4_result.json"),),
        (Path(dir_path, "data", "ical", "ical5"), Path(dir_path, "data", "ical", "ical5_result.json"),),
    ],
)
def test_complete_parsing(raw_file, results_file):
    """Tests for Ical parser."""
    with open(raw_file) as file_obj:
        parser = ICal(raw=file_obj.read())

    parsed_notifications = parser.process()[0]

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    assert json.loads(parsed_notifications.to_json()) == expected_result


@pytest.mark.parametrize(
    "raw_file, exception",
    [
        (Path(dir_path, "data", "ical", "ical_no_account"), MissingMandatoryFields,),
        (Path(dir_path, "data", "ical", "ical_no_maintenance_id"), MissingMandatoryFields,),
        (Path(dir_path, "data", "ical", "ical_no_stamp"), ParsingError,),
        (Path(dir_path, "data", "ical", "ical_no_start"), ParsingError,),
        (Path(dir_path, "data", "ical", "ical_no_end"), ParsingError,),
    ],
)
def test_errored_parsing(raw_file, exception):
    """Tests for Ical parser."""
    with open(raw_file) as file_obj:
        parser = ICal(raw=file_obj.read())

    with pytest.raises(exception):
        parser.process()
