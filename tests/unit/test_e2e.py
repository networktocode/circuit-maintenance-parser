"""Tests for End to End library usage."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.errors import ProviderError
from circuit_maintenance_parser.constants import EMAIL_HEADER_DATE, EMAIL_HEADER_SUBJECT

# pylint: disable=duplicate-code
from circuit_maintenance_parser.provider import (
    Equinix,
    GenericProvider,
    AquaComms,
    AWS,
    BSO,
    Cogent,
    Colt,
    EUNetworks,
    GTT,
    HGC,
    Lumen,
    Megaport,
    NTT,
    Momentum,
    PacketFabric,
    Seaborn,
    Sparkle,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Zayo,
)

dir_path = os.path.dirname(os.path.realpath(__file__))

GENERIC_ICAL_DATA_PATH = Path(dir_path, "data", "ical", "ical1")
GENERIC_ICAL_RESULT_PATH = Path(dir_path, "data", "ical", "ical1_result.json")


@pytest.mark.parametrize(
    "provider_class, test_data_files, result_parse_files",
    [
        # GenericProvider
        (
            GenericProvider,
            [
                ("ical", GENERIC_ICAL_DATA_PATH),
            ],
            [
                GENERIC_ICAL_RESULT_PATH,
            ],
        ),
        # AquaComms
        (
            AquaComms,
            [
                ("email", Path(dir_path, "data", "aquacomms", "aquacomms1.eml")),
            ],
            [
                Path(dir_path, "data", "aquacomms", "aquacomms1_result.json"),
            ],
        ),
        # AWS
        (
            AWS,
            [
                ("email", Path(dir_path, "data", "aws", "aws1.eml")),
            ],
            [
                Path(dir_path, "data", "aws", "aws1_result.json"),
            ],
        ),
        (
            AWS,
            [
                ("email", Path(dir_path, "data", "aws", "aws2.eml")),
            ],
            [
                Path(dir_path, "data", "aws", "aws2_result.json"),
            ],
        ),
        # BSO
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso3.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso3_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso4.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso4_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso5.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso5_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso6.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso6_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            BSO,
            [
                ("html", Path(dir_path, "data", "bso", "bso7.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "bso", "bso7_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Cogent
        (
            Cogent,
            [
                ("html", Path(dir_path, "data", "cogent", "cogent1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "cogent", "cogent1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Cogent,
            [
                ("html", Path(dir_path, "data", "cogent", "cogent2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "cogent", "cogent2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Colt
        (
            Colt,
            [
                ("email", Path(dir_path, "data", "colt", "colt3.eml")),
            ],
            [
                Path(dir_path, "data", "colt", "colt3_result.json"),
            ],
        ),
        (
            Colt,
            [
                ("email", Path(dir_path, "data", "colt", "colt4.eml")),
            ],
            [
                Path(dir_path, "data", "colt", "colt4_result.json"),
            ],
        ),
        (
            Colt,
            [
                ("email", Path(dir_path, "data", "colt", "colt5.eml")),
            ],
            [
                Path(dir_path, "data", "colt", "colt5_result.json"),
            ],
        ),
        (
            Colt,
            [
                ("email", Path(dir_path, "data", "colt", "colt6.eml")),
            ],
            [
                Path(dir_path, "data", "colt", "colt6_result.json"),
            ],
        ),
        (
            Colt,
            [
                ("email", Path(dir_path, "data", "colt", "colt7.eml")),
            ],
            [
                Path(dir_path, "data", "colt", "colt7_result.json"),
            ],
        ),
        # Equinix
        (
            Equinix,
            [("email", Path(dir_path, "data", "equinix", "equinix1.eml"))],
            [Path(dir_path, "data", "equinix", "equinix1_result_combined.json")],
        ),
        (
            Equinix,
            [("email", Path(dir_path, "data", "equinix", "equinix3.eml"))],
            [Path(dir_path, "data", "equinix", "equinix3_result_combined.json")],
        ),
        (
            Equinix,
            [("email", Path(dir_path, "data", "equinix", "equinix4.eml"))],
            [Path(dir_path, "data", "equinix", "equinix4_result_combined.json")],
        ),
        # EUNetworks
        (
            EUNetworks,
            [
                ("ical", GENERIC_ICAL_DATA_PATH),
            ],
            [
                GENERIC_ICAL_RESULT_PATH,
            ],
        ),
        # EXA / GTT
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt1_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt2_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt3.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt3_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt3_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt4.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt4_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt4_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt5.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt5_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt5_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("html", Path(dir_path, "data", "gtt", "gtt6.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "gtt", "gtt6_email_subject")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt6_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            GTT,
            [
                ("email", Path(dir_path, "data", "gtt", "gtt7.eml")),
            ],
            [
                Path(dir_path, "data", "gtt", "gtt7_result.json"),
            ],
        ),
        # HGC
        (
            HGC,
            [
                ("email", Path(dir_path, "data", "hgc", "hgc1.eml")),
                ("email", Path(dir_path, "data", "hgc", "hgc2.eml")),
            ],
            [
                Path(dir_path, "data", "hgc", "hgc1_result.json"),
                Path(dir_path, "data", "hgc", "hgc2_result.json"),
            ],
        ),
        # Lumen
        (
            Lumen,
            [
                ("html", Path(dir_path, "data", "lumen", "lumen1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "lumen", "subject_work_planned")),
            ],
            [
                Path(dir_path, "data", "lumen", "lumen1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Lumen,
            [
                ("html", Path(dir_path, "data", "lumen", "lumen2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "lumen", "subject_work_planned")),
            ],
            [
                Path(dir_path, "data", "lumen", "lumen2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Lumen,
            [
                ("html", Path(dir_path, "data", "lumen", "lumen3.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "lumen", "subject_work_planned")),
            ],
            [
                Path(dir_path, "data", "lumen", "lumen3_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Lumen,
            [
                ("html", Path(dir_path, "data", "lumen", "lumen4.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
                (EMAIL_HEADER_SUBJECT, Path(dir_path, "data", "lumen", "subject_work_planned")),
            ],
            [
                Path(dir_path, "data", "lumen", "lumen4_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Megaport
        (
            Megaport,
            [
                ("html", Path(dir_path, "data", "megaport", "megaport1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "megaport", "megaport1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Megaport,
            [
                ("html", Path(dir_path, "data", "megaport", "megaport2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "megaport", "megaport2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Momentum
        (
            Momentum,
            [
                ("email", Path(dir_path, "data", "momentum", "momentum1.eml")),
            ],
            [
                Path(dir_path, "data", "momentum", "momentum1_result.json"),
            ],
        ),
        # NTT
        (
            NTT,
            [
                ("ical", Path(dir_path, "data", "ntt", "ntt1")),
            ],
            [
                Path(dir_path, "data", "ntt", "ntt1_result.json"),
            ],
        ),
        (
            NTT,
            [
                ("ical", GENERIC_ICAL_DATA_PATH),
            ],
            [
                GENERIC_ICAL_RESULT_PATH,
            ],
        ),
        # PacketFabric
        (
            PacketFabric,
            [
                ("ical", GENERIC_ICAL_DATA_PATH),
            ],
            [
                GENERIC_ICAL_RESULT_PATH,
            ],
        ),
        # Seaborn
        (
            Seaborn,
            [
                ("email", Path(dir_path, "data", "seaborn", "seaborn1.eml")),
            ],
            [
                Path(dir_path, "data", "seaborn", "seaborn1_result.json"),
            ],
        ),
        (
            Seaborn,
            [
                ("email", Path(dir_path, "data", "seaborn", "seaborn2.eml")),
            ],
            [
                Path(dir_path, "data", "seaborn", "seaborn2_result.json"),
            ],
        ),
        (
            Seaborn,
            [
                ("email", Path(dir_path, "data", "seaborn", "seaborn3.eml")),
            ],
            [
                Path(dir_path, "data", "seaborn", "seaborn3_result.json"),
            ],
        ),
        # Sparkle
        (
            Sparkle,
            [
                ("email", Path(dir_path, "data", "sparkle", "sparkle1.eml")),
            ],
            [
                Path(dir_path, "data", "sparkle", "sparkle1_result.json"),
            ],
        ),
        # Telia
        (
            Telia,
            [
                ("ical", Path(dir_path, "data", "telia", "telia1")),
            ],
            [
                Path(dir_path, "data", "telia", "telia1_result.json"),
            ],
        ),
        (
            Telia,
            [
                ("ical", Path(dir_path, "data", "telia", "telia2")),
            ],
            [
                Path(dir_path, "data", "telia", "telia2_result.json"),
            ],
        ),
        # Telstra
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra3.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra3_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra4.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra4_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra5.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra5_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("html", Path(dir_path, "data", "telstra", "telstra6.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "telstra", "telstra6_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Telstra,
            [
                ("ical", GENERIC_ICAL_DATA_PATH),
            ],
            [
                GENERIC_ICAL_RESULT_PATH,
            ],
        ),
        # Turkcell
        (
            Turkcell,
            [
                ("html", Path(dir_path, "data", "turkcell", "turkcell1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "turkcell", "turkcell1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Turkcell,
            [
                ("html", Path(dir_path, "data", "turkcell", "turkcell2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "turkcell", "turkcell2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Verizon
        (
            Verizon,
            [
                ("html", Path(dir_path, "data", "verizon", "verizon1.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "verizon", "verizon1_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Verizon,
            [
                ("html", Path(dir_path, "data", "verizon", "verizon2.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "verizon", "verizon2_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        (
            Verizon,
            [
                ("html", Path(dir_path, "data", "verizon", "verizon3.html")),
                (EMAIL_HEADER_DATE, Path(dir_path, "data", "date", "email_date_1")),
            ],
            [
                Path(dir_path, "data", "verizon", "verizon3_result.json"),
                Path(dir_path, "data", "date", "email_date_1_result.json"),
            ],
        ),
        # Zayo
        (
            Zayo,
            [
                ("html", Path(dir_path, "data", "zayo", "zayo1.html")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo1_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("html", Path(dir_path, "data", "zayo", "zayo2.html")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo2_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("html", Path(dir_path, "data", "zayo", "zayo3.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo3_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo4.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo4_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo5.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo5_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo6.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo6_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo7.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo7_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo8.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo8_result.json"),
            ],
        ),
        (
            Zayo,
            [
                ("email", Path(dir_path, "data", "zayo", "zayo9.eml")),
            ],
            [
                Path(dir_path, "data", "zayo", "zayo9_result.json"),
            ],
        ),
    ],
)
def test_provider_get_maintenances(
    provider_class, test_data_files, result_parse_files
):  # pylint: disable=too-many-locals
    """End to End tests for various Providers."""
    extended_data = provider_class.get_extended_data()
    default_maintenance_data = {"uid": "0", "sequence": 1, "summary": ""}
    extended_data.update(default_maintenance_data)

    data = None
    for data_type, data_file in test_data_files:
        with open(data_file, "rb") as file_obj:
            if not data:
                if data_type in ["ical", "html"]:
                    data = NotificationData.init_from_raw(data_type, file_obj.read())
                elif data_type in ["email"]:
                    data = NotificationData.init_from_email_bytes(file_obj.read())
            else:
                data.add_data_part(data_type, file_obj.read())

    parsed_notifications = provider_class().get_maintenances(data)
    notifications_json = []
    for parsed_notification in parsed_notifications:
        notifications_json.append(json.loads(parsed_notification.to_json()))

    expected_result = []
    for result_parse_file in result_parse_files:
        with open(result_parse_file, encoding="utf-8") as res_file:
            partial_result_data = json.load(res_file)
            if not expected_result:
                expected_result = partial_result_data
            else:
                expected_result[0].update(partial_result_data[0])

    for result in expected_result:
        temp_res = result.copy()
        result.update(extended_data)
        result.update(temp_res)

    assert notifications_json == expected_result


@pytest.mark.parametrize(
    "provider_class, data_type, data_file, exception, error_message",
    [
        (
            GenericProvider,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_account"),
            ProviderError,
            """\
Failed creating Maintenance notification for GenericProvider.
Details:
- Processor SimpleProcessor from GenericProvider failed due to: 1 validation error for Maintenance\naccount\n  field required (type=value_error.missing)
""",
        ),
        (
            GenericProvider,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_maintenance_id"),
            ProviderError,
            """\
Failed creating Maintenance notification for GenericProvider.
Details:
- Processor SimpleProcessor from GenericProvider failed due to: 1 validation error for Maintenance
maintenance_id
  field required (type=value_error.missing)
""",
        ),
        (
            GenericProvider,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_stamp"),
            ProviderError,
            """\
Failed creating Maintenance notification for GenericProvider.
Details:
- Processor SimpleProcessor from GenericProvider failed due to: 'NoneType' object has no attribute 'dt'
""",
        ),
        (
            GenericProvider,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_start"),
            ProviderError,
            """\
Failed creating Maintenance notification for GenericProvider.
Details:
- Processor SimpleProcessor from GenericProvider failed due to: 'NoneType' object has no attribute 'dt'
""",
        ),
        (
            GenericProvider,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_end"),
            ProviderError,
            """\
Failed creating Maintenance notification for GenericProvider.
Details:
- Processor SimpleProcessor from GenericProvider failed due to: 'NoneType' object has no attribute 'dt'
""",
        ),
        (
            Telstra,
            "ical",
            Path(dir_path, "data", "ical", "ical_no_account"),
            ProviderError,
            """\
Failed creating Maintenance notification for Telstra.
Details:
- Processor SimpleProcessor from Telstra failed due to: 1 validation error for Maintenance\naccount\n  field required (type=value_error.missing)
- Processor CombinedProcessor from Telstra failed due to: None of the supported parsers for processor CombinedProcessor (EmailDateParser, HtmlParserTelstra1) was matching any of the provided data types (ical).
""",
        ),
        # Zayo
        (
            Zayo,
            "html",
            Path(dir_path, "data", "zayo", "zayo_missing_maintenance_id.html"),
            ProviderError,
            """\
Failed creating Maintenance notification for Zayo.
Details:
- Processor CombinedProcessor from Zayo failed due to: 1 validation error for Maintenance
maintenance_id
  String is empty or 'None' (type=value_error)
""",
        ),
        (
            Zayo,
            "html",
            Path(dir_path, "data", "zayo", "zayo_bad_html.html"),
            ProviderError,
            """\
Failed creating Maintenance notification for Zayo.
Details:
- Processor CombinedProcessor from Zayo failed due to: HtmlParserZayo1 parser was not able to extract the expected data for each maintenance.
  - Raw content: b'Maintenance Ticket #: aaa\\n'
  - Result: [{}]
""",
        ),
    ],
)
def test_errored_provider_process(provider_class, data_type, data_file, exception, error_message):
    """End to End negative tests."""
    extended_data = provider_class.get_extended_data()
    # TODO: check how to make data optional from Pydantic do not initialized?
    default_maintenance_data = {"stamp": None, "uid": "0", "sequence": 1, "summary": ""}
    extended_data.update(default_maintenance_data)

    with open(data_file, "rb") as file_obj:
        if data_type in ["ical", "html"]:
            data = NotificationData.init_from_raw(data_type, file_obj.read())
        elif data_type in ["email"]:
            data = NotificationData.init_from_email_bytes(file_obj.read())

    with pytest.raises(exception) as exc:
        provider_class().get_maintenances(data)

    assert len(exc.value.related_exceptions) == len(provider_class._processors)  # pylint: disable=protected-access
    assert str(exc.value) == error_message
