#!/usr/bin/env python3
"""Fix coverage.xml for SonarQube compatibility.

SonarQube's Cobertura parser rejects:
1. <line number="0"> entries (invalid line number)
2. Line numbers that exceed the actual file's line count

Usage: fix_coverage.py <coverage.xml> <source_root>
"""
import os
import sys
import xml.etree.ElementTree as ET


def count_lines(filepath: str) -> int:
    """Count actual lines in a file."""
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def resolve_path(filename: str, source_root: str) -> int:
    """Try multiple path strategies to find the file and return its line count."""
    candidates = [
        # Strategy 1: direct join (filename relative to source_root)
        os.path.join(source_root, filename),
        # Strategy 2: filename is absolute
        filename,
        # Strategy 3: strip first path component (e.g. strip "app/" prefix)
        os.path.join(source_root, *filename.split(os.sep)[1:]),
        # Strategy 4: filename relative to cwd
        filename,
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return count_lines(path)
    return 0


def fix_coverage_xml(xml_path: str, source_root: str) -> None:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    total_removed = 0

    for cls in root.findall(".//class"):
        filename = cls.get("filename", "")
        if not filename:
            continue

        max_lines = resolve_path(filename, source_root)

        lines_elem = cls.find("lines")
        if lines_elem is None:
            continue

        to_remove = []
        for line in lines_elem.findall("line"):
            try:
                n = int(line.get("number", "0"))
            except ValueError:
                to_remove.append(line)
                continue
            # Remove line 0 or (when we know the file size) out-of-range lines
            if n <= 0 or (max_lines > 0 and n > max_lines):
                to_remove.append(line)

        for line in to_remove:
            lines_elem.remove(line)
            total_removed += 1

    if total_removed:
        print(f"fix_coverage.py: removed {total_removed} invalid line entries", flush=True)

    tree.write(xml_path, encoding="unicode", xml_declaration=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <coverage.xml> <source_root>")
        sys.exit(1)

    # Change to source_root so relative paths work
    os.chdir(sys.argv[2])
    fix_coverage_xml(sys.argv[1], sys.argv[2])
