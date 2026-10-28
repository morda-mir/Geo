"""Export the active shared routing policy as small Mihomo rule providers.

Read the existing compiled assets; never rebuild or modify Happ/INCY files.
The existing Happ workflow remains the sole writer of dist/*.dat.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path

from build_morda_geo_happ import read_varint

ROOT = Path(__file__).resolve().parent
POLICY_FIELDS = ('BlockSites', 'BlockIp', 'ProxySites', 'ProxyIp', 'DirectSites', 'DirectIp')
OUTPUTS = {
    'block-domains.txt': ('BlockSites', 'domain'),
    'proxy-domains.txt': ('ProxySites', 'domain'),
    'direct-domains.txt': ('DirectSites', 'domain'),
    'proxy-ips.txt': ('ProxyIp', 'ip'),
    'direct-ips.txt': ('DirectIp', 'ip'),
}
DOMAIN_TYPES = {0: 'DOMAIN-KEYWORD', 1: 'DOMAIN-REGEX', 2: 'DOMAIN-SUFFIX', 3: 'DOMAIN'}


def fields(data: bytes):
    pos = 0
    while pos < len(data):
        key, pos = read_varint(data, pos)
        number, wire = key >> 3, key & 7
        if number == 0:
            raise ValueError('Invalid protobuf field zero')
        if wire == 0:
            value, pos = read_varint(data, pos)
        elif wire == 2:
            size, pos = read_varint(data, pos)
            end = pos + size
            if end > len(data):
                raise ValueError('Truncated protobuf field')
            value, pos = data[pos:end], end
        elif wire in (1, 5):
            end = pos + (8 if wire == 1 else 4)
            if end > len(data):
                raise ValueError('Truncated protobuf fixed field')
            value, pos = data[pos:end], end
        else:
            raise ValueError(f'Unsupported protobuf wire type {wire}')
        yield number, wire, value


def selected_entries(path: Path, wanted: set[str]) -> dict[str, bytes]:
    result = {}
    seen = set()
    for number, wire, payload in fields(path.read_bytes()):
        if (number, wire) != (1, 2):
            continue
        code = next((v.decode('ascii').upper() for n, w, v in fields(payload) if (n, w) == (1, 2)), None)
        if not code or code in seen:
            raise ValueError(f'{path.name}: missing/duplicate category {code}')
        seen.add(code)
        if code in wanted:
            result[code] = payload
    missing = wanted - result.keys()
    if missing:
        raise ValueError(f'{path.name}: missing compiled categories {sorted(missing)}')
    return result


def domain_rules(entry: bytes) -> list[str]:
    result = []
    for number, wire, domain in fields(entry):
        if (number, wire) != (2, 2):
            continue
        kind, value = 0, None
        for n, w, v in fields(domain):
            if (n, w) == (1, 0):
                kind = v
            elif (n, w) == (2, 2):
                value = v.decode('utf-8')
            elif n == 3:
                raise ValueError('Attributed geosite entries require an explicit conversion policy')
        if kind not in DOMAIN_TYPES or not value or '\n' in value or '\r' in value:
            raise ValueError('Invalid/unsupported geosite domain')
        if ',' in value:
            raise ValueError('Comma-containing rules require an explicit text-format conversion policy')
        result.append(f'{DOMAIN_TYPES[kind]},{value}')
    return result


def ip_rules(entry: bytes) -> list[str]:
    result = []
    for number, wire, cidr in fields(entry):
        if (number, wire) == (3, 0) and cidr:
            raise ValueError('Inverse GeoIP categories cannot be flattened')
        if (number, wire) != (2, 2):
            continue
        packed, prefix = None, 0
        for n, w, v in fields(cidr):
            if (n, w) == (1, 2):
                packed = v
            elif (n, w) == (2, 0):
                prefix = v
        if packed is None or len(packed) not in (4, 16):
            raise ValueError('Invalid GeoIP address')
        network = ipaddress.ip_network(f'{ipaddress.ip_address(packed)}/{prefix}', strict=False)
        result.append(str(network))
    return result


def category_codes(profile: dict, field: str, prefix: str) -> list[str]:
    values = profile[field]
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise ValueError(f'{field}: expected unique category references')
    codes = []
    for value in values:
        if not isinstance(value, str) or not value.lower().startswith(prefix + ':'):
            raise ValueError(f'{field}: unsupported routing reference {value!r}')
        codes.append(value.split(':', 1)[1].upper())
    return codes


def build(root: Path = ROOT) -> dict[str, bytes]:
    profile = json.loads((root / 'dist/incy-routing-v2.json').read_text('utf-8'))
    if profile['RouteOrder'] != 'block-proxy-direct' or profile['GlobalProxy'] != 'false':
        raise ValueError('The template must be reviewed before changing route order or default action')
    if profile['DomainStrategy'] != 'AsIs' or profile.get('BlockIp'):
        raise ValueError('Unsupported DNS strategy or nonempty BlockIp')
    required_sites = {code for field in POLICY_FIELDS if field.endswith('Sites')
                      for code in category_codes(profile, field, 'geosite')}
    required_ips = {code for field in POLICY_FIELDS if field.endswith('Ip')
                    for code in category_codes(profile, field, 'geoip')}
    sites = selected_entries(root / 'dist/geosite.dat', required_sites)
    ips = selected_entries(root / 'dist/geoip.dat', required_ips)
    outputs = {}
    manifest = {'schema': 1, 'routeOrder': profile['RouteOrder'], 'defaultAction': 'DIRECT',
                'domainStrategy': profile['DomainStrategy'], 'categories': {f: profile[f] for f in POLICY_FIELDS},
                'dns': {k: profile[k] for k in ('RemoteDNSDomain', 'RemoteDNSIP', 'DomesticDNSType', 'DomesticDNSIP')},
                'inputs': {}, 'files': {}}
    for filename, (field, kind) in OUTPUTS.items():
        source = sites if kind == 'domain' else ips
        prefix = 'geosite' if kind == 'domain' else 'geoip'
        converter = domain_rules if kind == 'domain' else ip_rules
        rules = sorted({rule for code in category_codes(profile, field, prefix) for rule in converter(source[code])})
        if not rules:
            raise ValueError(f'{filename}: empty active rule set')
        if field == 'ProxyIp' and any(ipaddress.ip_network(r).prefixlen == 0 for r in rules):
            raise ValueError('Catch-all proxy IP ranges are not allowed')
        content = ('\n'.join(rules) + '\n').encode('utf-8')
        if len(content) > 1024 * 1024:
            raise ValueError(f'{filename}: unexpectedly large rule set')
        outputs[filename] = content
        manifest['files'][filename] = {'rules': len(rules), 'bytes': len(content),
                                       'sha256': hashlib.sha256(content).hexdigest()}
    for name in ('geosite.dat', 'geoip.dat', 'incy-routing-v2.json'):
        manifest['inputs'][name] = hashlib.sha256((root / 'dist' / name).read_bytes()).hexdigest()
    outputs['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if committed providers need rebuilding')
    args = parser.parse_args()
    outputs = build()
    destination = ROOT / 'dist/mihomo'
    if not args.check:
        destination.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        path = destination / name
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise SystemExit(f'Outdated generated provider: {name}')
        else:
            path.write_bytes(content)
        print(f'{name}: {len(content)} bytes')


if __name__ == '__main__':
    main()
