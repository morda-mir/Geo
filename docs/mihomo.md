# Shared Morda rules for RabbitHole / Mihomo

`build_morda_mihomo.py` exports only the categories referenced by
`dist/incy-routing-v2.json` from the existing `dist/geosite.dat` and
`dist/geoip.dat`. Both the original and V2 INCY profiles currently use the same
routing policy. Existing compiled assets and INCY/Happ profiles are read-only
inputs to this exporter.

## Published providers

Canonical base URL:
`https://raw.githubusercontent.com/morda-mir/Geo/main/dist/mihomo/`

| File | Mihomo behavior | Policy field |
|---|---|---|
| `block-domains.txt` | classical | BlockSites |
| `proxy-domains.txt` | classical | ProxySites |
| `proxy-ips.txt` | ipcidr | ProxyIp |
| `direct-domains.txt` | classical | DirectSites |
| `direct-ips.txt` | ipcidr | DirectIp |

Use `format: text` with these files. `manifest.json` records category references,
input SHA-256 values, provider hashes, counts, and the shared DNS policy.

Domain matching preserves the compiled domain type: exact, suffix, keyword,
or regular expression. IP providers preserve both IPv4 and IPv6 CIDRs.
Unsupported attributed/inverse categories, missing/duplicate categories,
empty lists, and catch-all proxy IP ranges fail the build rather than silently
changing routing behavior.

## Routing and DNS

The profile uses this order:

1. Block domains → REJECT.
2. Proxy domains and selected proxy IP ranges → selected VPN server.
3. Direct domains and private IP ranges → DIRECT.
4. Unmatched traffic → DIRECT.

Apply `no-resolve` to the IP `RULE-SET` entries to preserve the shared `AsIs`
policy instead of resolving every unrelated domain solely to test IP lists.
Roblox, Discord voice cloud ranges, and legacy Brawl Stars IPs are not reactivated.
The current proxy IP categories are Telegram, Facebook/Meta, Twitter, and the
narrow custom OpenAI set.

Remote DNS uses the Google DoH policy through the selected VPN group. Direct
domestic DNS remains Yandex UDP `77.88.8.8`. Node/bootstrap DNS must be independent
of the VPN group to avoid a dependency loop. Changes to the shared DNS policy or
route order require reviewing the served YAML template as well as the providers.

On RabbitHole select **Routing → Default**, which uses the provider's configured
rules. Off/Global sends all traffic through a selected proxy; Included/Excluded
replace provider rules with user selections. The app's separate built-in service
lists are not substitutes for these Morda providers.

HTTP providers can update every 86400 seconds while the core is running. A
deployment may relay the canonical files through the existing subscription host
so first-time downloads do not depend on direct GitHub access. Such a relay must
be restricted to the five provider names and manifest, not arbitrary URLs.

## Build and updates

```sh
python3 -m unittest discover -s tests -v
python3 build_morda_mihomo.py
python3 build_morda_mihomo.py --check
```

The existing `build-happ-compatible-geo` workflow remains the sole writer of
`dist/*.dat`. A successful non-PR run triggers `build-mihomo-routing`, which
checks out current main and exports providers from the newly generated assets.
Changes to the Mihomo exporter/tests/workflow can run the new workflow directly
without rebuilding Happ assets. Both workflows share the `geo-dist-main`
concurrency group. The new workflow commits only `dist/mihomo`.

The provider export is deterministic and has no external dependencies. Updating
domain/IP source rules continues to use the existing production workflow.
