"""Tests for Zayo parser."""
import json
import os
from pathlib import Path

import pytest

from circuitmaint_parser.parsers.zayo import ParserZayo
from circuitmaint_parser.errors import MissingMandatoryFields, ParsingError

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "raw_file, results_file",
    [(Path(dir_path, "data", "zayo", "zayo1.html"), Path(dir_path, "data", "zayo", "zayo1_result.json"),),],
)
def test_complete_parsing(raw_file, results_file):
    """Tests for Zayo parser."""
    with open(raw_file) as file_obj:
        parser = ParserZayo(raw=file_obj.read())

    parsed_notifications = parser.process()[0]

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    assert json.loads(parsed_notifications.to_json()) == expected_result


# pylint: disable=duplicate-code
@pytest.mark.parametrize(
    "raw_file, exception",
    [
        (Path(dir_path, "data", "zayo", "zayo_missing_maintenance_id.html"), MissingMandatoryFields,),
        (Path(dir_path, "data", "zayo", "zayo_bad_html.html"), ParsingError,),
    ],
)
def test_errored_parsing(raw_file, exception):
    """Tests for Ical parser."""
    with open(raw_file) as file_obj:
        parser = ParserZayo(raw=file_obj.read())

    with pytest.raises(exception):
        parser.process()
