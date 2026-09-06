import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate import build_client_conf, build_server_conf, ensure_keys
from wgkeys import generate_keypair, public_key_for


class KeyTests(unittest.TestCase):
    def test_generate_keypair_round_trips(self):
        priv, pub = generate_keypair()
        self.assertEqual(public_key_for(priv), pub)

    def test_generate_keypair_is_random(self):
        priv1, _ = generate_keypair()
        priv2, _ = generate_keypair()
        self.assertNotEqual(priv1, priv2)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "server": {
                "endpoint": "vpn.example.com:51820",
                "address": "10.10.0.1/24",
                "listen_port": 51820,
                "dns": "1.1.1.1",
                "private_key": None,
                "public_key": None,
            },
            "peers": [
                {"name": "test-peer", "allowed_ips": "10.10.0.2/32",
                 "private_key": None, "public_key": None},
            ],
        }
        ensure_keys(self.config["server"])
        for peer in self.config["peers"]:
            ensure_keys(peer)

    def test_ensure_keys_fills_in_both_keys(self):
        self.assertIsNotNone(self.config["server"]["private_key"])
        self.assertIsNotNone(self.config["server"]["public_key"])

    def test_ensure_keys_derives_public_from_existing_private(self):
        priv, pub = generate_keypair()
        entry = {"private_key": priv, "public_key": None}
        ensure_keys(entry)
        self.assertEqual(entry["public_key"], pub)

    def test_server_conf_contains_all_peers(self):
        conf = build_server_conf(self.config)
        self.assertIn("[Interface]", conf)
        self.assertIn(self.config["peers"][0]["public_key"], conf)
        self.assertIn("10.10.0.2/32", conf)

    def test_client_conf_points_back_at_server(self):
        conf = build_client_conf(self.config, self.config["peers"][0])
        self.assertIn(self.config["server"]["public_key"], conf)
        self.assertIn("vpn.example.com:51820", conf)
        self.assertIn(self.config["peers"][0]["private_key"], conf)

    def test_idempotent_key_generation_via_cli_like_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "peers.json")
            with open(config_path, "w") as f:
                json.dump(self.config, f)

            with open(config_path) as f:
                reloaded = json.load(f)
            for peer in reloaded["peers"]:
                ensure_keys(peer)  # should be a no-op, keys already present

            self.assertEqual(reloaded["peers"][0]["private_key"],
                              self.config["peers"][0]["private_key"])


if __name__ == "__main__":
    unittest.main()
