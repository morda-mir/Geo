from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_GEOIP = ROOT / 'src' / 'geoip'
DIST = ROOT / 'dist'
UPSTREAM_GEOIP = DIST / 'geoip.upstream.dat'
OUTPUT_GEOIP = DIST / 'geoip.dat'

GO_MOD = '''module morda-geoip-append

go 1.24

require (
    github.com/v2fly/v2ray-core/v5 v5.39.0
    google.golang.org/protobuf v1.36.10
)
'''

GO_MAIN = '''package main

import (
    "bufio"
    "fmt"
    "net/netip"
    "os"
    "path/filepath"
    "sort"
    "strings"

    routercommon "github.com/v2fly/v2ray-core/v5/app/router/routercommon"
    "google.golang.org/protobuf/proto"
)

func parseCIDR(line string) (netip.Prefix, bool, error) {
    line = strings.TrimSpace(line)
    if line == "" || strings.HasPrefix(line, "#") {
        return netip.Prefix{}, false, nil
    }
    if i := strings.Index(line, "#"); i >= 0 {
        line = strings.TrimSpace(line[:i])
    }
    if line == "" {
        return netip.Prefix{}, false, nil
    }
    prefix, err := netip.ParsePrefix(line)
    if err != nil {
        return netip.Prefix{}, false, err
    }
    return prefix.Masked(), true, nil
}

func main() {
    if len(os.Args) != 4 {
        panic("usage: append-geoip <upstream.dat> <src-geoip-dir> <output.dat>")
    }
    upstreamPath := os.Args[1]
    srcDir := os.Args[2]
    outputPath := os.Args[3]

    data, err := os.ReadFile(upstreamPath)
    if err != nil {
        panic(err)
    }

    list := &routercommon.GeoIPList{}
    if err := proto.Unmarshal(data, list); err != nil {
        panic(err)
    }

    entriesByCode := map[string]*routercommon.GeoIP{}
    for _, entry := range list.Entry {
        entriesByCode[strings.ToUpper(entry.CountryCode)] = entry
    }

    files, err := filepath.Glob(filepath.Join(srcDir, "*.txt"))
    if err != nil {
        panic(err)
    }
    sort.Strings(files)

    for _, file := range files {
        code := strings.ToUpper(strings.TrimSuffix(filepath.Base(file), filepath.Ext(file)))
        entry := entriesByCode[code]
        if entry == nil {
            entry = &routercommon.GeoIP{CountryCode: code}
            entriesByCode[code] = entry
            list.Entry = append(list.Entry, entry)
        }

        f, err := os.Open(file)
        if err != nil {
            panic(err)
        }
        scanner := bufio.NewScanner(f)
        for scanner.Scan() {
            prefix, ok, err := parseCIDR(scanner.Text())
            if err != nil {
                f.Close()
                panic(fmt.Errorf("%s: %w", file, err))
            }
            if !ok {
                continue
            }
            addr := prefix.Addr()
            if addr.Is4() {
                ip4 := addr.As4()
                entry.Cidr = append(entry.Cidr, &routercommon.CIDR{Ip: ip4[:], Prefix: uint32(prefix.Bits())})
            } else if addr.Is6() {
                ip16 := addr.As16()
                entry.Cidr = append(entry.Cidr, &routercommon.CIDR{Ip: ip16[:], Prefix: uint32(prefix.Bits())})
            }
        }
        if err := scanner.Err(); err != nil {
            f.Close()
            panic(err)
        }
        f.Close()
    }

    out, err := proto.MarshalOptions{Deterministic: true}.Marshal(list)
    if err != nil {
        panic(err)
    }
    if err := os.WriteFile(outputPath, out, 0644); err != nil {
        panic(err)
    }
}
'''


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def main() -> None:
    if not UPSTREAM_GEOIP.exists():
        raise SystemExit(f'missing upstream geoip: {UPSTREAM_GEOIP}')
    if not SRC_GEOIP.exists():
        shutil.copy2(UPSTREAM_GEOIP, OUTPUT_GEOIP)
        return

    with tempfile.TemporaryDirectory(prefix='morda-geoip-') as tmp:
        work = Path(tmp)
        (work / 'go.mod').write_text(GO_MOD)
        (work / 'main.go').write_text(GO_MAIN)
        run(['go', 'mod', 'download'], cwd=work)
        run(['go', 'run', '.', str(UPSTREAM_GEOIP), str(SRC_GEOIP), str(OUTPUT_GEOIP)], cwd=work)


if __name__ == '__main__':
    main()
