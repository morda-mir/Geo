from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
SRC_GEOSITE = ROOT / 'src' / 'geosite'
UPSTREAM_GEOIP_URL = 'https://raw.githubusercontent.com/runetfreedom/russia-blocked-geoip/release/geoip.dat'

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


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='morda-geo-happ-') as tmp:
        build_geosite(Path(tmp))
        build_geoip()


if __name__ == '__main__':
    main()
