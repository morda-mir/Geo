#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "geosite"
OUT_FILE = ROOT / "dist" / "geosite.dat"

TYPE_MAP = {
    "plain": 0,
    "regexp": 1,
    "regex": 1,
    "domain": 2,
    "full": 3,
}


def varint(value: int) -> bytes:
    out = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            out.append(to_write | 0x80)
        else:
            out.append(to_write)
            return bytes(out)


def field_key(field_number: int, wire_type: int) -> bytes:
    return varint((field_number << 3) | wire_type)


def bytes_field(field_number: int, payload: bytes) -> bytes:
    return field_key(field_number, 2) + varint(len(payload)) + payload


def string_field(field_number: int, value: str) -> bytes:
    return bytes_field(field_number, value.encode("utf-8"))


def int_field(field_number: int, value: int) -> bytes:
    return field_key(field_number, 0) + varint(value)


def domain_message(kind: int, value: str) -> bytes:
    # v2ray/ext/router/routercommon/common.proto:
    # message Domain { enum Type { Plain=0; Regex=1; Domain=2; Full=3; } Type type=1; string value=2; ... }
    return int_field(1, kind) + string_field(2, value)


def geosite_message(code: str, rules: list[tuple[int, str]]) -> bytes:
    payload = string_field(1, code)
    for kind, value in rules:
        payload += bytes_field(2, domain_message(kind, value))
    return payload


def geosite_list(entries: list[tuple[str, list[tuple[int, str]]]]) -> bytes:
    payload = bytearray()
    for code, rules in entries:
        payload += bytes_field(1, geosite_message(code, rules))
    return bytes(payload)


def parse_source(path: Path) -> list[tuple[int, str]]:
    rules: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()

    for raw in path.read_text("utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"{path}: invalid rule without prefix: {raw!r}")

        prefix, value = line.split(":", 1)
        prefix = prefix.strip().lower()
        value = value.strip()
        if not value:
            raise ValueError(f"{path}: empty rule value: {raw!r}")
        if prefix not in TYPE_MAP:
            raise ValueError(f"{path}: unsupported rule type {prefix!r}: {raw!r}")

        item = (TYPE_MAP[prefix], value)
        if item not in seen:
            seen.add(item)
            rules.append(item)

    return rules


def main() -> None:
    if not SRC_DIR.exists():
        raise SystemExit(f"missing source dir: {SRC_DIR}")

    entries: list[tuple[str, list[tuple[int, str]]]] = []
    for path in sorted(SRC_DIR.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        code = path.name.upper()
        rules = parse_source(path)
        if rules:
            entries.append((code, rules))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_bytes(geosite_list(entries))

    total_rules = sum(len(rules) for _, rules in entries)
    print(f"built {OUT_FILE} with {len(entries)} categories and {total_rules} rules")
    for code, rules in entries:
        print(f"  {code}: {len(rules)}")


if __name__ == "__main__":
    main()
