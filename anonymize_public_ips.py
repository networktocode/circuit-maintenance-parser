"""Helper script to check and clean IP Addresses in test data."""
import re
import os
import sys
import argparse
import fileinput

TEST_DATA_PATH = os.path.join("tests", "unit", "data")
REPLACE_TEXT_IPV4 = "192.0.2.1"
REPLACE_TEXT_IPV6 = "2001:DB8::1"


# Reference: https://gist.github.com/dfee/6ed3a4b05cfe7a6faf40a2102408d5d8
IPV4SEG = r"(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])"
IPV4_ADDR_REGEX = r"(?:(?:" + IPV4SEG + r"\.){3,3}" + IPV4SEG + r")"
IPV6SEG = r"(?:(?:[0-9a-fA-F]){1,4})"
IPV6GROUPS = (
    r"(?:" + IPV6SEG + r":){7,7}" + IPV6SEG,  # 1:2:3:4:5:6:7:8
    r"(?:" + IPV6SEG + r":){1,7}:",  # 1::                                 1:2:3:4:5:6:7::
    r"(?:" + IPV6SEG + r":){1,6}:" + IPV6SEG,  # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
    r"(?:" + IPV6SEG + r":){1,5}(?::" + IPV6SEG + r"){1,2}",  # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
    r"(?:" + IPV6SEG + r":){1,4}(?::" + IPV6SEG + r"){1,3}",  # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
    r"(?:" + IPV6SEG + r":){1,3}(?::" + IPV6SEG + r"){1,4}",  # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
    r"(?:" + IPV6SEG + r":){1,2}(?::" + IPV6SEG + r"){1,5}",  # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
    IPV6SEG + r":(?:(?::" + IPV6SEG + r"){1,6})",  # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
    r":(?:(?::" + IPV6SEG + r"){1,7}|:)",  # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
    r"fe80:(?::"
    + IPV6SEG
    + r"){0,4}%[0-9a-zA-Z]{1,}",  # fe80::7:8%eth0     fe80::7:8%1  (link-local IPv6 addresses with zone index)
    r"::(?:ffff(?::0{1,4}){0,1}:){0,1}[^\s:]"
    + IPV4_ADDR_REGEX,  # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255 (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
    r"(?:"
    + IPV6SEG
    + r":){1,4}:[^\s:]"
    + IPV4_ADDR_REGEX,  # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)
IPV6_ADDR_REGEX = "|".join([f"(?:{g})" for g in IPV6GROUPS[::-1]])  # Reverse rows for greedy match


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
