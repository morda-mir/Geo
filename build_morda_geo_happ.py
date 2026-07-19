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


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    previous_hashes = {asset: file_sha256(asset) for asset in GEO_ASSETS}

    with tempfile.TemporaryDirectory(prefix='morda-geo-happ-') as tmp:
        build_geosite(Path(tmp))
        build_geoip()

    current_hashes = {asset: file_sha256(asset) for asset in GEO_ASSETS}
    write_sha256_sidecars()
    if current_hashes != previous_hashes:
        update_incy_timestamps()


if __name__ == '__main__':
    main()
