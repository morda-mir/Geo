from __future__ import annotations

import ipaddress
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_GEOIP = ROOT / 'src' / 'geoip'
DIST = ROOT / 'dist'
UPSTREAM_GEOIP = DIST / 'geoip.upstream.dat'
OUTPUT_GEOIP = DIST / 'geoip.dat'

# Xray/V2Ray geoip.dat uses protobuf:
# GeoIPList { repeated GeoIP entry = 1; }
# GeoIP { string country_code = 1; repeated CIDR cidr = 2; bool reverse_match = 3; }
# CIDR { bytes ip = 1; uint32 prefix = 2; }
# For our use case the upstream file is treated as an opaque GeoIPList and we append
# extra top-level GeoIP entries. This avoids Go/protoc dependencies in GitHub Actions.


def encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError('varint cannot encode negative values')
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def field_bytes(field_number: int, data: bytes) -> bytes:
    return encode_varint((field_number << 3) | 2) + encode_varint(len(data)) + data


def field_varint(field_number: int, value: int) -> bytes:
    return encode_varint(field_number << 3) + encode_varint(value)


def cidr_message(network: ipaddress._BaseNetwork) -> bytes:
    return field_bytes(1, network.network_address.packed) + field_varint(2, network.prefixlen)


def geoip_entry(country_code: str, networks: list[ipaddress._BaseNetwork]) -> bytes:
    payload = bytearray()
    payload += field_bytes(1, country_code.encode('ascii'))
    for network in networks:
        payload += field_bytes(2, cidr_message(network))
    return field_bytes(1, bytes(payload))


def load_networks(path: Path) -> list[ipaddress._BaseNetwork]:
    networks: list[ipaddress._BaseNetwork] = []
    for line_no, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.split('#', 1)[0].strip()
        if not line:
            continue
        try:
            networks.append(ipaddress.ip_network(line, strict=False))
        except ValueError as exc:
            raise ValueError(f'{path}:{line_no}: invalid CIDR {line!r}') from exc
    return networks


def main() -> None:
    if not UPSTREAM_GEOIP.exists():
        raise SystemExit(f'missing upstream geoip: {UPSTREAM_GEOIP}')
    if not SRC_GEOIP.exists():
        shutil.copy2(UPSTREAM_GEOIP, OUTPUT_GEOIP)
        return

    output = bytearray(UPSTREAM_GEOIP.read_bytes())
    for path in sorted(SRC_GEOIP.glob('*.txt')):
        country_code = path.stem.upper()
        networks = load_networks(path)
        if not networks:
            continue
        output += geoip_entry(country_code, networks)

    OUTPUT_GEOIP.write_bytes(bytes(output))


if __name__ == '__main__':
    main()
