"""Helper script to check and clean IP Addresses in test data."""
import re
import os
import sys
import argparse
import fileinput

TEST_DATA_PATH = os.path.join("tests", "unit", "data")
REPLACE_TEXT_IPV4 = "192.0.2.1"
REPLACE_TEXT_IPV6 = "2001:DB8::1"
IPV4_ADDR_REGEX = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)
IPV6_ADDR_REGEX = re.compile(r"(?<![:.\w])(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}(?![:.\w])")


def replace(filename, search_exp, replace_exp):
    """Replace line when a substitution is needed."""
    report = ""
    for line in fileinput.input(filename, inplace=True):
        newline = re.sub(search_exp, replace_exp, line)
        sys.stdout.write(newline)
        if line != newline:
            if not report:
                report = f"IP Address found and replaced in {filename}\n"
            report += f"  - {line}"
    return report


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Clean IP Addresses.")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    clean = args.clean

    ip_found = False
    for (dirpath, _, files) in os.walk(TEST_DATA_PATH):
        for file in files:
            report = ""
            if file.endswith((".eml", ".html", ".json")):
                filename = os.path.join(dirpath, file)
                if not clean:
                    with open(filename, "r", encoding="utf-8") as test_file:
                        content = test_file.readlines()
                        for content_line in content:
                            content_new = re.sub(IPV4_ADDR_REGEX, REPLACE_TEXT_IPV4, content_line)
                            content_new = re.sub(IPV6_ADDR_REGEX, REPLACE_TEXT_IPV6, content_new)
                            if content_line != content_new:
                                if not report:
                                    report = f"IP Address found in {filename}\n"
                                report += f"  - {content_line}"
                else:
                    report = replace(filename, IPV4_ADDR_REGEX, REPLACE_TEXT_IPV4)
                    report += replace(filename, IPV6_ADDR_REGEX, REPLACE_TEXT_IPV6)
                if report:
                    ip_found = True
                    print(report)

    if ip_found and not clean:
        print("\nHINT - you can clean up these IPs with 'invoke clean-anonymize-ips'")
        sys.exit(1)
    elif ip_found and clean:
        print(f"\nIP addresses have been changed to {REPLACE_TEXT_IPV4} and {REPLACE_TEXT_IPV6}")
    else:
        print("Only documentation IPs found.")


if __name__ == "__main__":
    main()
