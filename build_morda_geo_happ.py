from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
SRC_GEOSITE = ROOT / 'src' / 'geosite'
SRC_GEOIP = ROOT / 'src' / 'geoip'
UPSTREAM_GEOIP_URL = 'https://raw.githubusercontent.com/runetfreedom/russia-blocked-geoip/release/geoip.dat'
INCY_ROUTING_PROFILES = (
    DIST / 'incy-routing.json',
    DIST / 'incy-routing-v2.json',
)
GEO_ASSETS = (DIST / 'geosite.dat', DIST / 'geoip.dat')

# Build geosite from local rules and geoip from production upstream plus local custom categories.
# Source categories merged into categories already used by Happ profiles.
# Result: users keep geosite:MORDA-PROXY, but short-video rules are included in it.
MERGE_GEOSITE = {
    'MORDA-TT': 'MORDA-PROXY',
}


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text('utf-8').splitlines()


def append_unique_lines(target: Path, source: Path) -> None:
    target_lines = read_lines(target)
    seen = {line.strip() for line in target_lines if line.strip() and not line.strip().startswith('#')}

    out = list(target_lines)
    source_lines = read_lines(source)
    extra: list[str] = []
    for raw in source_lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line not in seen:
            seen.add(line)
            extra.append(line)

    if extra:
        if out and out[-1].strip():
            out.append('')
        out.append(f'# merged from {source.name}')
        out.extend(extra)
        target.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')


def prepare_geosite_data(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)

    for src in SRC_GEOSITE.iterdir():
        if src.is_file():
            shutil.copy2(src, data_dir / src.name)

    for source_code, target_code in MERGE_GEOSITE.items():
        source = data_dir / source_code
        target = data_dir / target_code
        if source.exists() and target.exists():
            append_unique_lines(target, source)


def build_geosite(work: Path) -> None:
    repo = work / 'domain-list-community'
    run(['git', 'clone', '--depth', '1', 'https://github.com/v2fly/domain-list-community.git', str(repo)])

    data_dir = work / 'geosite-data'
    prepare_geosite_data(data_dir)

    run(['go', 'mod', 'download'], cwd=repo)
    run(['go', 'run', './', f'--datapath={data_dir}'], cwd=repo)
    shutil.copy2(repo / 'dlc.dat', DIST / 'geosite.dat')


def build_geoip() -> None:
    upstream = DIST / 'geoip.upstream.dat'
    run(['curl', '-L', '--fail', '-o', str(upstream), UPSTREAM_GEOIP_URL])
    run(['python3', 'scripts/append_custom_geoip.py'], cwd=ROOT)
    upstream.unlink(missing_ok=True)


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256_sidecars() -> None:
    for asset in GEO_ASSETS:
        digest = file_sha256(asset)
        if digest is None:
            raise FileNotFoundError(f'Missing generated asset: {asset}')
        sidecar = asset.with_name(f'{asset.name}.sha256')
        with sidecar.open('w', encoding='ascii', newline='\n') as output:
            output.write(f'{digest}\n')


def update_incy_timestamps() -> None:
    timestamp = str(int(time.time()))
    for routing_profile in INCY_ROUTING_PROFILES:
        if not routing_profile.exists():
            raise FileNotFoundError(f'Missing INCY routing profile: {routing_profile}')

        profile = json.loads(routing_profile.read_text(encoding='utf-8'))
        profile['LastUpdated'] = timestamp
        routing_profile.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )


def read_varint(data: bytes, start: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while start < len(data) and shift <= 63:
        octet = data[start]
        start += 1
        value |= (octet & 0x7f) << shift
        if not octet & 0x80:
            return value, start
        shift += 7
    raise ValueError('Malformed protobuf varint')


def compiled_category_codes(path: Path) -> set[str]:
    # Both Xray GeoIPList and GeoSiteList use repeated entry=1;
    # each entry stores its category code as the first string field=1.
    payload = path.read_bytes()
    codes: set[str] = set()
    pos = 0
    while pos < len(payload):
        key, pos = read_varint(payload, pos)
        field_number, wire_type = key >> 3, key & 7
        if wire_type == 2:
            length, pos = read_varint(payload, pos)
            end = pos + length
            if end > len(payload):
                raise ValueError(f'{path}: malformed length-delimited field')
            if field_number == 1:
                inner = payload[pos:end]
                inner_key, inner_pos = read_varint(inner, 0)
                if inner_key != 10:
                    raise ValueError(f'{path}: missing category name in entry')
                name_size, inner_pos = read_varint(inner, inner_pos)
                code = inner[inner_pos:inner_pos + name_size].decode('ascii').upper()
                if not code:
                    raise ValueError(f'{path}: empty category name')
                if code in codes:
                    raise ValueError(f'{path}: duplicate category {code}')
                codes.add(code)
            pos = end
        elif wire_type == 0:
            _, pos = read_varint(payload, pos)
        elif wire_type in (1, 5):
            pos += 8 if wire_type == 1 else 4
        else:
            raise ValueError(f'{path}: unsupported protobuf wire type {wire_type}')
    return codes


def validate_incy_profiles() -> None:
    # Validate the built .dat files, not just source filenames. This catches
    # missing upstream categories (e.g. FACEBOOK/TWITTER) before publication.
    if (DIST / 'geoip.dat').stat().st_size < 10 * 1024 * 1024:
        raise ValueError('geoip.dat suspiciously small: upstream base may be missing')
    if (DIST / 'geosite.dat').stat().st_size < 5 * 1024:
        raise ValueError('geosite.dat suspiciously small')

    geosite_codes = compiled_category_codes(DIST / 'geosite.dat')
    geoip_codes = compiled_category_codes(DIST / 'geoip.dat')
    required_geoip = {'PRIVATE', 'TELEGRAM', 'FACEBOOK', 'TWITTER'}
    missing_base = required_geoip - geoip_codes
    if missing_base:
        raise ValueError(f'geoip.dat missing upstream categories: {sorted(missing_base)}')

    custom_geosite = {p.name.upper() for p in SRC_GEOSITE.iterdir() if p.is_file() and not p.name.startswith('.')}
    custom_geoip = {
        p.stem.removesuffix('-ip').upper()
        for p in SRC_GEOIP.iterdir() if p.is_file() and not p.name.startswith('.')
    }
    for label, expected, actual in (
        ('geosite', custom_geosite, geosite_codes),
        ('geoip', custom_geoip, geoip_codes),
    ):
        missing = expected - actual
        if missing:
            raise ValueError(f'{label}.dat missing custom categories: {sorted(missing)}')

    route_fields = {
        'DirectSites': ('geosite:', geosite_codes),
        'ProxySites': ('geosite:', geosite_codes),
        'BlockSites': ('geosite:', geosite_codes),
        'DirectIp': ('geoip:', geoip_codes),
        'ProxyIp': ('geoip:', geoip_codes),
        'BlockIp': ('geoip:', geoip_codes),
    }

    for routing_profile in INCY_ROUTING_PROFILES:
        profile = json.loads(routing_profile.read_text(encoding='utf-8'))
        for field, (prefix, available_codes) in route_fields.items():
            entries = profile.get(field)
            if not isinstance(entries, list):
                raise ValueError(f'{routing_profile}:{field} must be a list')
            if len(entries) != len(set(entries)):
                raise ValueError(f'{routing_profile}:{field} contains duplicates')
            for entry in entries:
                if not isinstance(entry, str):
                    raise ValueError(f'{routing_profile}:{field} contains a non-string entry')
                if entry.lower().startswith(prefix):
                    code = entry.split(':', 1)[1].upper()
                    if code not in available_codes:
                        raise ValueError(
                            f'{routing_profile}:{field} references missing {prefix}{code}'
                        )

        proxy_sites = set(profile['ProxySites'])
        if {'geosite:MORDA-PROXY', 'geosite:MORDA-TT'} <= proxy_sites:
            raise ValueError(
                f'{routing_profile}:MORDA-TT is already merged into MORDA-PROXY'
            )


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='morda-geo-happ-') as tmp:
        build_geosite(Path(tmp))
        build_geoip()

    write_sha256_sidecars()
    validate_incy_profiles()
    # A workflow run means either routing sources, build logic, or a published
    # profile changed. Always advance the profile version so installed clients
    # can observe non-geodata changes such as DNS or route-list updates too.
    update_incy_timestamps()


if __name__ == '__main__':
    main()
