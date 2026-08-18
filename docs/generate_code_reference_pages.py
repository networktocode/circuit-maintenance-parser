"""Generate the code reference page."""

from pathlib import Path

import mkdocs_gen_files

PACKAGE = "circuit_maintenance_parser"

with mkdocs_gen_files.open("code-reference.md", "w") as fd:
    print("# Code Reference\n", file=fd)
    for file_path in sorted(Path(PACKAGE).rglob("*.py")):
        parts = list(file_path.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        print(f"::: {'.'.join(parts)}", file=fd)
