# Current status

## Production-safe for desktop Happ

Use:

- `Geositeurl`: `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat`
- `Geoipurl`: `https://raw.githubusercontent.com/runetfreedom/russia-blocked-geoip/release/geoip.dat`

Working categories:

- `geosite:MORDA-PROXY`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`
- `geoip:private`
- `geoip:telegram`

## Important note

The custom `dist/geoip.dat` currently works on some mobile clients, but desktop Happ rejects it as invalid.
So for desktop Happ, use external `runetfreedom` geoip until a fully compatible custom geoip build is found.

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/runetfreedom/russia-blocked-geoip/release/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": [],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```
