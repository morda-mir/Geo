# Production routing policy

This document records compatibility constraints for the shared Morda routing
profile. Treat them as production requirements, not temporary implementation
details.

## Audience and distribution

- Publish routing profiles and geo assets through this GitHub repository.
- Maintain one shared routing profile for users in Russia and mainland China.
- Do not introduce country-specific profiles unless the product policy changes.
- Preserve a usable fallback: users who encounter a regional incompatibility can
  disable custom geo routing in the client.

## DNS compatibility baseline

- Remote/proxied destinations use Google DNS over HTTPS:
  `https://dns.google/dns-query`, bootstrapped with `8.8.8.8`.
- Domestic/direct destinations use Yandex DNS over UDP at `77.88.8.8`.
- Keep `DomainStrategy` set to `AsIs` while domain categories are maintained.
- Do not change the domestic resolver or its transport without testing the
  resulting profile from both Russia and mainland China.
- Reliability across the supported regions takes priority over changing the DNS
  transport solely for theoretical privacy or performance improvements.

## Roblox

- Roblox is not part of active proxy routing because it is directly accessible
  for the primary Russian audience.
- Keep `geoip:MORDA-ROBLOX` in generated assets temporarily so older installed
  profiles that still reference the category do not fail to load.
- Do not re-add Roblox domains or IPs to active routing without a new, observed
  access problem.

## Brawl Stars

- `geoip:MORDA-BRAWLSTARS` stays in generated assets for legacy profile compatibility.
- Do not activate its historical /32 cloud and Apple addresses in shared profiles;
  they can proxy unrelated services. Domain-only Supercell routes remain for now.

## Meta / Instagram / WhatsApp

- Use the upstream `geoip:facebook` category in active profiles to route observed
  IP-only Meta/Instagram UDP flows; keep primary service domains in MORDA-PROXY.
- This category also covers other Meta services. Verify in Happ logs and avoid
  adding broad Cloudflare/AWS/Google ranges to compensate for misses.

## X / Twitter

- Route official product domains and upstream `geoip:twitter` IP category.
- Keep raw IP routing narrow and verify no unrelated traffic is caught.

## Discord voice

- Discord web, gateway, media, and voice domains remain proxied.
- Active `geoip:MORDA-DISCORD` routing is disabled because voice endpoints are
  dynamic and migrating across shared cloud infrastructure. Maintaining broad
  provider ranges conflicts with the minimum-proxy policy and can destabilize
  unrelated traffic.
- Keep `geoip:MORDA-DISCORD` in generated assets temporarily so older installed
  profiles that still reference the category do not fail to load.
- Voice connectivity is best-effort in restricted networks and can fail even
  while text, authentication, web, and media continue to work.
- Do not replace the category with catch-all UDP, broad cloud-provider ranges,
  or forced per-application proxying in the shared production profile.

## Safe rollout rules

- Preserve published URLs, profile names, and category names during normal
  maintenance.
- Keep compatibility categories in generated assets for at least one rollout
  after removing them from active profile references.
- Advance `LastUpdated` whenever profiles, routing sources, or generated geo
  assets change so installed clients can refresh predictably.
- Validate JSON parsing and real compiled `.dat` category references before publishing.
- Preserve existing source categories and old profile URLs until legacy clients are migrated.
- Let the production build workflow regenerate `dist/*.dat`; do not hand-edit
  generated binary assets.
