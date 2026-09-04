#!/usr/bin/env python3
"""Generate a WireGuard server config and per-peer client configs from a peer list.

Usage:
    python generate.py peers.json --out ./out
"""
import argparse
import json
import os

from wgkeys import generate_keypair, public_key_for

DEFAULT_CLIENT_ALLOWED_IPS = "0.0.0.0/0, ::/0"
DEFAULT_PERSISTENT_KEEPALIVE = 25


def ensure_keys(entry: dict) -> None:
    """Fill in private/public keys on a server or peer entry, generating if missing."""
    if not entry.get("private_key"):
        priv, pub = generate_keypair()
        entry["private_key"] = priv
        entry["public_key"] = pub
    elif not entry.get("public_key"):
        entry["public_key"] = public_key_for(entry["private_key"])


def build_server_conf(config: dict) -> str:
    server = config["server"]
    lines = [
        "[Interface]",
        f"PrivateKey = {server['private_key']}",
        f"Address = {server['address']}",
        f"ListenPort = {server.get('listen_port', 51820)}",
    ]
    for peer in config["peers"]:
        lines += [
            "",
            "[Peer]",
            f"# {peer['name']}",
            f"PublicKey = {peer['public_key']}",
            f"AllowedIPs = {peer['allowed_ips']}",
        ]
    return "\n".join(lines) + "\n"


def build_client_conf(config: dict, peer: dict) -> str:
    server = config["server"]
    lines = [
        "[Interface]",
        f"PrivateKey = {peer['private_key']}",
        f"Address = {peer['allowed_ips']}",
    ]
    if server.get("dns"):
        lines.append(f"DNS = {server['dns']}")
    lines += [
        "",
        "[Peer]",
        f"PublicKey = {server['public_key']}",
        f"Endpoint = {server['endpoint']}",
        f"AllowedIPs = {peer.get('client_allowed_ips', DEFAULT_CLIENT_ALLOWED_IPS)}",
        f"PersistentKeepalive = {peer.get('persistent_keepalive', DEFAULT_PERSISTENT_KEEPALIVE)}",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_file", help="Path to a peers.json file")
    parser.add_argument("--out", default="./out", help="Output directory (default: ./out)")
    args = parser.parse_args()

    with open(args.config_file) as f:
        config = json.load(f)

    ensure_keys(config["server"])
    for peer in config["peers"]:
        ensure_keys(peer)

    # Write generated keys back so re-running is idempotent (peers keep their identity).
    with open(args.config_file, "w") as f:
        json.dump(config, f, indent=2)

    clients_dir = os.path.join(args.out, "clients")
    os.makedirs(clients_dir, exist_ok=True)

    with open(os.path.join(args.out, "server.conf"), "w") as f:
        f.write(build_server_conf(config))
    print(f"Wrote {os.path.join(args.out, 'server.conf')}")

    for peer in config["peers"]:
        path = os.path.join(clients_dir, f"{peer['name']}.conf")
        with open(path, "w") as f:
            f.write(build_client_conf(config, peer))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
