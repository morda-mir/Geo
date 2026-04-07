from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
SRC_GEOSITE = ROOT / 'src' / 'geosite'
SRC_GEOIP = ROOT / 'src' / 'geoip'


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def build_geosite(work: Path) -> None:
    repo = work / 'domain-list-community'
    run(['git', 'clone', '--depth', '1', 'https://github.com/v2fly/domain-list-community.git', str(repo)])
    data_dir = work / 'geosite-data'
    data_dir.mkdir(parents=True, exist_ok=True)
    for src in SRC_GEOSITE.iterdir():
        if src.is_file():
            shutil.copy2(src, data_dir / src.name)
    run(['go', 'mod', 'download'], cwd=repo)
    run(['go', 'run', './', f'--datapath={data_dir}'], cwd=repo)
    shutil.copy2(repo / 'dlc.dat', DIST / 'geosite.dat')


def build_geoip(work: Path) -> None:
    repo = work / 'geoip'
    run(['git', 'clone', '--depth', '1', 'https://github.com/v2fly/geoip.git', str(repo)])
    config = {
        'input': [
            {
                'type': 'private',
                'action': 'add'
            },
            {
                'type': 'text',
                'action': 'add',
                'args': {
                    'name': 'telegram',
                    'uri': str((SRC_GEOIP / 'telegram-ip.txt').resolve()),
                },
            }
        ],
        'output': [
            {
                'type': 'v2rayGeoIPDat',
                'action': 'output',
                'args': {
                    'outputDir': str(DIST.resolve()),
                    'outputName': 'geoip.dat',
                    'wantedList': ['private', 'telegram'],
                },
            }
        ],
    }
    config_path = work / 'geoip-config-happ.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    run(['go', 'mod', 'download'], cwd=repo)
    run(['go', 'run', './', '-c', str(config_path)], cwd=repo)


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='morda-geo-happ-') as tmp:
        work = Path(tmp)
        build_geosite(work)
        build_geoip(work)


if __name__ == '__main__':
    main()
