import importlib.util
import hashlib
import ipaddress
import json
from pathlib import Path
import tempfile
import unittest

import build_morda_mihomo as builder

spec = importlib.util.spec_from_file_location('geoip_helpers', Path(__file__).resolve().parents[1] / 'scripts/append_custom_geoip.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
B, V = helpers.field_bytes, helpers.field_varint


def site(code, *domains):
    return B(1, B(1, code.encode()) + b''.join(B(2, V(1, kind) + B(2, value.encode())) for kind, value in domains))


class ExportTests(unittest.TestCase):
    def test_domain_types_preserve_exact_suffix_and_regex_semantics(self):
        data = B(1, b'TEST') + b''.join(B(2, V(1, kind) + B(2, value.encode())) for kind, value in [
            (3, 'exact.example'), (2, 'suffix.example'), (1, r'^app-\d+\.example$'), (0, 'keyword')])
        self.assertEqual(builder.domain_rules(data), ['DOMAIN,exact.example', 'DOMAIN-SUFFIX,suffix.example',
                         r'DOMAIN-REGEX,^app-\d+\.example$', 'DOMAIN-KEYWORD,keyword'])

    def test_ipv4_ipv6_and_inverse_categories(self):
        networks = [ipaddress.ip_network('192.0.2.0/24'), ipaddress.ip_network('2001:db8::/32')]
        payload = B(1, b'TEST') + b''.join(B(2, helpers.cidr_message(n)) for n in networks)
        self.assertEqual(builder.ip_rules(payload), [str(n) for n in networks])
        with self.assertRaisesRegex(ValueError, 'Inverse'):
            builder.ip_rules(payload + V(3, 1))

    def test_missing_duplicate_and_truncated_categories_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'geosite.dat'
            path.write_bytes(site('ONE', (2, 'one.example')))
            with self.assertRaisesRegex(ValueError, 'missing compiled'):
                builder.selected_entries(path, {'TWO'})
            path.write_bytes(site('ONE') * 2)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                builder.selected_entries(path, {'ONE'})
            path.write_bytes(b'\x0a\xff\xff')
            with self.assertRaises(ValueError):
                builder.selected_entries(path, {'ONE'})

    def test_export_is_deterministic_and_does_not_modify_source_assets(self):
        root = Path(__file__).resolve().parents[1]
        inputs = {name: (root / 'dist' / name).read_bytes() for name in ('geosite.dat', 'geoip.dat', 'incy-routing-v2.json')}
        first = builder.build(root)
        self.assertEqual(first, builder.build(root))
        for name, content in inputs.items():
            self.assertEqual((root / 'dist' / name).read_bytes(), content)
        manifest = json.loads(first['manifest.json'])
        self.assertEqual(manifest['defaultAction'], 'DIRECT')
        self.assertEqual(manifest['routeOrder'], 'block-proxy-direct')
        profile_bytes = inputs['incy-routing-v2.json'].replace(b'\r\n', b'\n')
        self.assertEqual(manifest['inputs']['incy-routing-v2.json'], hashlib.sha256(profile_bytes).hexdigest())
        self.assertIn('geoip:facebook', manifest['categories']['ProxyIp'])
        self.assertIn('geoip:twitter', manifest['categories']['ProxyIp'])
        for removed in ('geoip:MORDA-ROBLOX', 'geoip:MORDA-DISCORD', 'geoip:MORDA-BRAWLSTARS'):
            self.assertNotIn(removed, manifest['categories']['ProxyIp'])
        self.assertIn(b'DOMAIN-SUFFIX,tiktok.com', first['proxy-domains.txt'])


if __name__ == '__main__':
    unittest.main()
