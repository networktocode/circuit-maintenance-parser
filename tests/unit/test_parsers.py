"""Tests generic for parser."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.parser import ICal, EmailDateParser
from circuit_maintenance_parser.parsers.aquacomms import HtmlParserAquaComms1, SubjectParserAquaComms1
from circuit_maintenance_parser.parsers.aws import SubjectParserAWS1, TextParserAWS1
from circuit_maintenance_parser.parsers.bso import HtmlParserBSO1
from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.colt import CsvParserColt1, SubjectParserColt1, SubjectParserColt2
from circuit_maintenance_parser.parsers.equinix import HtmlParserEquinix, SubjectParserEquinix
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.hgc import HtmlParserHGC1, HtmlParserHGC2
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.momentum import HtmlParserMomentum1
from circuit_maintenance_parser.parsers.seaborn import (
    HtmlParserSeaborn1,
    HtmlParserSeaborn2,
    SubjectParserSeaborn1,
    SubjectParserSeaborn2,
)
from circuit_maintenance_parser.parsers.sparkle import HtmlParserSparkle1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1, HtmlParserTelstra2
from circuit_maintenance_parser.parsers.turkcell import HtmlParserTurkcell1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import SubjectParserZayo1, HtmlParserZayo1


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "parser_class, raw_file, results_file",
    [
        # iCal
        (
            ICal,
            Path(dir_path, "data", "ical", "ical1"),
            Path(dir_path, "data", "ical", "ical1_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical2"),
            Path(dir_path, "data", "ical", "ical2_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical3"),
            Path(dir_path, "data", "ical", "ical3_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical4"),
            Path(dir_path, "data", "ical", "ical4_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical5"),
            Path(dir_path, "data", "ical", "ical5_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical6"),
            Path(dir_path, "data", "ical", "ical6_result.json"),
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical7"),
            Path(dir_path, "data", "ical", "ical7_result.json"),
        ),
        # AquaComms
        (
            HtmlParserAquaComms1,
            Path(dir_path, "data", "aquacomms", "aquacomms1.eml"),
            Path(dir_path, "data", "aquacomms", "aquacomms1_html_parser_result.json"),
        ),
        (
            SubjectParserAquaComms1,
            Path(dir_path, "data", "aquacomms", "aquacomms1.eml"),
            Path(dir_path, "data", "aquacomms", "aquacomms1_subject_parser_result.json"),
        ),
        # AWS
        (
            TextParserAWS1,
            Path(dir_path, "data", "aws", "aws1.eml"),
            Path(dir_path, "data", "aws", "aws1_text_parser_result.json"),
        ),
        (
            SubjectParserAWS1,
            Path(dir_path, "data", "aws", "aws1.eml"),
            Path(dir_path, "data", "aws", "aws1_subject_parser_result.json"),
        ),
        (
            TextParserAWS1,
            Path(dir_path, "data", "aws", "aws2.eml"),
            Path(dir_path, "data", "aws", "aws2_text_parser_result.json"),
        ),
        (
            SubjectParserAWS1,
            Path(dir_path, "data", "aws", "aws2.eml"),
            Path(dir_path, "data", "aws", "aws2_subject_parser_result.json"),
        ),
        (
            TextParserAWS1,
            Path(dir_path, "data", "aws", "aws3.eml"),
            Path(dir_path, "data", "aws", "aws3_text_parser_result.json"),
        ),
        # BSO
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso1.html"),
            Path(dir_path, "data", "bso", "bso1_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso2.html"),
            Path(dir_path, "data", "bso", "bso2_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso3.html"),
            Path(dir_path, "data", "bso", "bso3_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso4.html"),
            Path(dir_path, "data", "bso", "bso4_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso5.html"),
            Path(dir_path, "data", "bso", "bso5_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso6.html"),
            Path(dir_path, "data", "bso", "bso6_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso7.html"),
            Path(dir_path, "data", "bso", "bso7_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso1_first.eml"),
            Path(dir_path, "data", "bso", "bso1_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso2_start.eml"),
            Path(dir_path, "data", "bso", "bso2_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso3_update.eml"),
            Path(dir_path, "data", "bso", "bso3_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso4_end.eml"),
            Path(dir_path, "data", "bso", "bso4_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso5_reminder_multiple_ts.eml"),
            Path(dir_path, "data", "bso", "bso5_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso6_cancel.eml"),
            Path(dir_path, "data", "bso", "bso6_result.json"),
        ),
        (
            HtmlParserBSO1,
            Path(dir_path, "data", "bso", "bso7_backup_ts.eml"),
            Path(dir_path, "data", "bso", "bso7_result.json"),
        ),
        # Cogent
        (
            HtmlParserCogent1,
            Path(dir_path, "data", "cogent", "cogent1.html"),
            Path(dir_path, "data", "cogent", "cogent1_result.json"),
        ),
        (
            HtmlParserCogent1,
            Path(dir_path, "data", "cogent", "cogent2.html"),
            Path(dir_path, "data", "cogent", "cogent2_result.json"),
        ),
        # Colt
        (
            CsvParserColt1,
            Path(dir_path, "data", "colt", "colt2.csv"),
            Path(dir_path, "data", "colt", "colt2_result.json"),
        ),
        (
            SubjectParserColt1,
            Path(dir_path, "data", "colt", "colt4.eml"),
            Path(dir_path, "data", "colt", "colt4_subject_parser_1_result.json"),
        ),
        (
            SubjectParserColt2,
            Path(dir_path, "data", "colt", "colt5.eml"),
            Path(dir_path, "data", "colt", "colt5_subject_parser_2_result.json"),
        ),
        (
            SubjectParserColt2,
            Path(dir_path, "data", "colt", "colt6.eml"),
            Path(dir_path, "data", "colt", "colt6_subject_parser_2_result.json"),
        ),
        (
            SubjectParserColt1,
            Path(dir_path, "data", "colt", "colt7.eml"),
            Path(dir_path, "data", "colt", "colt7_subject_parser_1_result.json"),
        ),
        # Equinix
        (
            HtmlParserEquinix,
            Path(dir_path, "data", "equinix", "equinix1.eml"),
            Path(dir_path, "data", "equinix", "equinix1_result1.json"),
        ),
        (
            SubjectParserEquinix,
            Path(dir_path, "data", "equinix", "equinix2.eml"),
            Path(dir_path, "data", "equinix", "equinix2_result.json"),
        ),
        (
            HtmlParserEquinix,
            Path(dir_path, "data", "equinix", "equinix3.eml"),
            Path(dir_path, "data", "equinix", "equinix3_result.json"),
        ),
        (
            HtmlParserEquinix,
            Path(dir_path, "data", "equinix", "equinix4.eml"),
            Path(dir_path, "data", "equinix", "equinix4_result.json"),
        ),
        (
            HtmlParserEquinix,
            Path(dir_path, "data", "equinix", "equinix5.eml"),
            Path(dir_path, "data", "equinix", "equinix5_result.json"),
        ),
        # GTT
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt1.html"),
            Path(dir_path, "data", "gtt", "gtt1_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt2.html"),
            Path(dir_path, "data", "gtt", "gtt2_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt3.html"),
            Path(dir_path, "data", "gtt", "gtt3_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt4.html"),
            Path(dir_path, "data", "gtt", "gtt4_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt5.html"),
            Path(dir_path, "data", "gtt", "gtt5_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt6.html"),
            Path(dir_path, "data", "gtt", "gtt6_result.json"),
        ),
        (
            HtmlParserGTT1,
            Path(dir_path, "data", "gtt", "gtt7.eml"),
            Path(dir_path, "data", "gtt", "gtt7_html_parser_result.json"),
        ),
        # HGC
        (
            HtmlParserHGC1,
            Path(dir_path, "data", "hgc", "hgc1.eml"),
            Path(dir_path, "data", "hgc", "hgc1_html_result.json"),
        ),
        (
            HtmlParserHGC2,
            Path(dir_path, "data", "hgc", "hgc2.eml"),
            Path(dir_path, "data", "hgc", "hgc2_html_result.json"),
        ),
        # Lumen
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen1.html"),
            Path(dir_path, "data", "lumen", "lumen1_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen2.html"),
            Path(dir_path, "data", "lumen", "lumen2_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen3.html"),
            Path(dir_path, "data", "lumen", "lumen3_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen4.html"),
            Path(dir_path, "data", "lumen", "lumen4_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen5.html"),
            Path(dir_path, "data", "lumen", "lumen5_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen6.html"),
            Path(dir_path, "data", "lumen", "lumen6_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen7.html"),
            Path(dir_path, "data", "lumen", "lumen7_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen8.html"),
            Path(dir_path, "data", "lumen", "lumen8_result.json"),
        ),
        # Megaport
        (
            HtmlParserMegaport1,
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            HtmlParserMegaport1,
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # Momentum
        (
            HtmlParserMomentum1,
            Path(dir_path, "data", "momentum", "momentum1.eml"),
            Path(dir_path, "data", "momentum", "momentum1_html_parser_result.json"),
        ),
        # NTT
        (
            ICal,
            Path(dir_path, "data", "ntt", "ntt1"),
            Path(dir_path, "data", "ntt", "ntt1_result.json"),
        ),
        # Seaborn
        (
            HtmlParserSeaborn1,
            Path(dir_path, "data", "seaborn", "seaborn3.eml"),
            Path(dir_path, "data", "seaborn", "seaborn3_html_parser_result.json"),
        ),
        (
            HtmlParserSeaborn2,
            Path(dir_path, "data", "seaborn", "seaborn2.eml"),
            Path(dir_path, "data", "seaborn", "seaborn2_html_parser_result.json"),
        ),
        (
            SubjectParserSeaborn1,
            Path(dir_path, "data", "seaborn", "seaborn3.eml"),
            Path(dir_path, "data", "seaborn", "seaborn3_subject_parser_result.json"),
        ),
        (
            SubjectParserSeaborn2,
            Path(dir_path, "data", "seaborn", "seaborn2.eml"),
            Path(dir_path, "data", "seaborn", "seaborn2_subject_parser_result.json"),
        ),
        # Sparkle
        (
            HtmlParserSparkle1,
            Path(dir_path, "data", "sparkle", "sparkle1.eml"),
            Path(dir_path, "data", "sparkle", "sparkle1_html_parser_result.json"),
        ),
        # Telstra
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra3.html"),
            Path(dir_path, "data", "telstra", "telstra3_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra4.html"),
            Path(dir_path, "data", "telstra", "telstra4_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra5.html"),
            Path(dir_path, "data", "telstra", "telstra5_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra6.html"),
            Path(dir_path, "data", "telstra", "telstra6_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra7.html"),
            Path(dir_path, "data", "telstra", "telstra7_result.json"),
        ),
        (
            HtmlParserTelstra2,
            Path(dir_path, "data", "telstra", "telstra8.html"),
            Path(dir_path, "data", "telstra", "telstra8_result.json"),
        ),
        # Turkcell
        (
            HtmlParserTurkcell1,
            Path(dir_path, "data", "turkcell", "turkcell1.html"),
            Path(dir_path, "data", "turkcell", "turkcell1_result.json"),
        ),
        (
            HtmlParserTurkcell1,
            Path(dir_path, "data", "turkcell", "turkcell2.html"),
            Path(dir_path, "data", "turkcell", "turkcell2_result.json"),
        ),
        # Verizon
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon1.html"),
            Path(dir_path, "data", "verizon", "verizon1_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon2.html"),
            Path(dir_path, "data", "verizon", "verizon2_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon3.html"),
            Path(dir_path, "data", "verizon", "verizon3_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon4.html"),
            Path(dir_path, "data", "verizon", "verizon4_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon5.html"),
            Path(dir_path, "data", "verizon", "verizon5_result.json"),
        ),
        # Zayo
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo_subject_1.txt"),
            Path(dir_path, "data", "zayo", "zayo_subject_1_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo_subject_2.txt"),
            Path(dir_path, "data", "zayo", "zayo_subject_2_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo1.html"),
            Path(dir_path, "data", "zayo", "zayo1_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo2.html"),
            Path(dir_path, "data", "zayo", "zayo2_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo3.eml"),
            Path(dir_path, "data", "zayo", "zayo3_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo4.eml"),
            Path(dir_path, "data", "zayo", "zayo4_html_parser_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo4.eml"),
            Path(dir_path, "data", "zayo", "zayo4_subject_parser_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo5.eml"),
            Path(dir_path, "data", "zayo", "zayo5_html_parser_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo5.eml"),
            Path(dir_path, "data", "zayo", "zayo5_subject_parser_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo6.eml"),
            Path(dir_path, "data", "zayo", "zayo6_html_parser_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo6.eml"),
            Path(dir_path, "data", "zayo", "zayo6_subject_parser_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo7.eml"),
            Path(dir_path, "data", "zayo", "zayo7_html_parser_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo7.eml"),
            Path(dir_path, "data", "zayo", "zayo7_subject_parser_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo8.eml"),
            Path(dir_path, "data", "zayo", "zayo8_html_parser_result.json"),
        ),
        (
            SubjectParserZayo1,
            Path(dir_path, "data", "zayo", "zayo8_subject.txt"),
            Path(dir_path, "data", "zayo", "zayo8_subject_parser_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo9.eml"),
            Path(dir_path, "data", "zayo", "zayo9_html_parser_result.json"),
        ),
        # Email Date
        (
            EmailDateParser,
            Path(dir_path, "data", "date", "email_date_1"),
            Path(dir_path, "data", "date", "email_date_1_result.json"),
        ),
    ],
)
def test_parsers(parser_class, raw_file, results_file):
    """Tests various parser."""
    with open(raw_file, "rb") as file_obj:
        raw_data = file_obj.read()

    parsed_notifications = parser_class().parse(raw_data, parser_class.get_data_types()[0])

    with open(results_file, encoding="utf-8") as res_file:
        expected_result = json.load(res_file)

    if parser_class == EmailDateParser:
        assert parsed_notifications == [expected_result]
    else:
        assert parsed_notifications == expected_result


@pytest.mark.parametrize("parser_class", [ICal, EmailDateParser, HtmlParserZayo1, SubjectParserZayo1])
def test_parser_no_data(parser_class):
    """Test parser with no data."""
    with pytest.raises(ParserError):
        parser_class().parse(b"", parser_class._data_types[0])  # pylint: disable=protected-access
