"""Tests for objdump parser logic."""
import re
from embedded_analyzer.core.objdump_parser import ObjdumpParser


def _parse_sections_from_text(output: str):
    """Test helper: parse section info from objdump -h text output using regex patterns."""
    lines = output.strip().split("\n")
    sections = []
    pattern = r"^\s*(\d+)\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+(\S+)"
    for line in lines:
        match = re.match(pattern, line)
        if match:
            sections.append({
                "index": int(match.group(1)),
                "name": match.group(2),
                "size": int(match.group(3), 16),
            })
    return sections


SAMPLE_OBJDUMP_OUTPUT = """riscv64-unknown-elf-objdump: file format elf64-littleriscv

Sections:
Idx Name          Size      VMA               LMA               File off  Algn
  0 .text         000001e4  0000000000000000  0000000000000000  00000034  2**2
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  1 .data         00000014  0000000000000000  0000000000000000  00000218  2**2
                  CONTENTS, ALLOC, LOAD, DATA
  2 .bss          00000008  0000000000000000  0000000000000000  0000022c  2**0
                  ALLOC
  3 .ram_text     00000300  0000000000000000  0000000000000000  00000234  2**1
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  4 .comment      0000001d  0000000000000000  0000000000000000  00000534  2**0
                  CONTENTS, READONLY
"""


def test_parse_sections_from_sample():
    sections = _parse_sections_from_text(SAMPLE_OBJDUMP_OUTPUT)
    assert len(sections) == 5

    names = [s["name"] for s in sections]
    assert ".text" in names
    assert ".data" in names
    assert ".bss" in names
    assert ".ram_text" in names


def test_section_sizes():
    sections = _parse_sections_from_text(SAMPLE_OBJDUMP_OUTPUT)
    text = next(s for s in sections if s["name"] == ".text")
    assert text["size"] == 0x1e4

    ram_text = next(s for s in sections if s["name"] == ".ram_text")
    assert ram_text["size"] == 0x300

    data = next(s for s in sections if s["name"] == ".data")
    assert data["size"] == 0x14


def test_exact_section_name_matching():
    sections = _parse_sections_from_text(SAMPLE_OBJDUMP_OUTPUT)
    names = [s["name"] for s in sections]
    assert ".ram_text" in names
    assert ".comment" in names
    assert not any(n.startswith(".ram_text_") for n in names)