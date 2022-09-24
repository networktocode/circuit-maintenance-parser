"""Anonymize IPs."""
import os
import sys
import argparse
import fileinput
import random
import string
from netconan.ip_anonymization import IpAnonymizer, IpV6Anonymizer, anonymize_ip_addr  # type: ignore


TEST_DATA_PATH = os.path.join("tests", "unit", "data")

_DEFAULT_SALT_LENGTH = 16
_CHAR_CHOICES = string.ascii_letters + string.digits
SALT = "".join(random.choice(_CHAR_CHOICES) for _ in range(_DEFAULT_SALT_LENGTH))  # nosec

anonymizer4 = IpAnonymizer(SALT, None, preserve_addresses=["192.0.2.0/24"], preserve_suffix=None,)
anonymizer6 = IpV6Anonymizer(SALT, preserve_suffix=None)


def replace(filename):
    """Replace line when a substitution is needed."""
    partial_report = ""
    try:
        with open(filename, encoding="utf-8") as file:
            file.read()
    except (UnicodeDecodeError, RuntimeError) as error:
        return f"Warning: Not able to process {filename}: {error}\n"

    with fileinput.input(files=(filename,), inplace=True) as file:
        for line in file:
            newline = anonymize_ip_addr(anonymizer6, line, False)
            newline = anonymize_ip_addr(anonymizer4, newline, False)
            sys.stdout.write(newline)
            if line != newline:
                if not partial_report:
                    partial_report = f"IP Address found and replaced in {filename}\n"
                partial_report += f"  - {line}"

    return partial_report


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clean IP Addresses.")
    parser.add_argument("--provider", help="Provider folder name, under tests/unit/data to anonymize.", required=False)
    parser.add_argument("--file", help="Absolute filename name to anonymize.", required=False)
    args = parser.parse_args()

    if args.provider and args.file:
        print("Provider and File are mutually exclusive, choose one.")
        sys.exit(0)
    elif args.provider:
        path = os.path.join(TEST_DATA_PATH, args.provider)
    elif args.file:
        path = args.file
    else:
        path = TEST_DATA_PATH

    report = ""
    for (dirpath, _, files) in os.walk(path):
        for file in files:
            filename = os.path.join(dirpath, file)
            report += replace(filename)

    print(
        f"{report}" "\nIPv4 and IPv6 addresses have been anonymized.",
        " \nPlease, keep in mind that this could uncover some parsing dependencies on white spaces.",
    )


if __name__ == "__main__":
    main()
