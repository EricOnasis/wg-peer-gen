# wg-peer-gen

Generate a WireGuard server config and matching per-peer client configs — with QR codes for mobile
clients — from a single peer list. No `wg` binary required; key generation is pure Python
(X25519 via the `cryptography` library, verified byte-for-byte compatible with `wg genkey`/`wg pubkey`).

## Installation

```sh
pip install -r requirements.txt
```

## Usage

Copy the example peer list and edit it:

```sh
cp peers.example.json peers.json
```

```json
{
  "server": {
    "endpoint": "vpn.example.com:51820",
    "address": "10.10.0.1/24",
    "listen_port": 51820,
    "dns": "1.1.1.1",
    "private_key": null,
    "public_key": null
  },
  "peers": [
    {"name": "laptop-eric", "allowed_ips": "10.10.0.2/32"},
    {"name": "phone-eric", "allowed_ips": "10.10.0.3/32"}
  ]
}
```

Leave `private_key`/`public_key` as `null` — they're generated on first run and written back into
the file, so re-running is idempotent: existing peers keep the same keys, only new peers get fresh
ones.

```sh
python generate.py peers.json --out ./out
```

This writes:

- `out/server.conf` — drop into your WireGuard server's config.
- `out/clients/<name>.conf` — one per peer, each with its own private key and pointed at the server.

Add `--qr` to also generate a QR code PNG per client (scan with the WireGuard mobile app instead of
transferring the file), or `--qr-terminal` to print it straight to the terminal as ASCII:

```sh
python generate.py peers.json --out ./out --qr-terminal
```

### Per-peer options

- `allowed_ips` — the peer's tunnel address, also used as its `AllowedIPs` entry on the server side.
- `client_allowed_ips` — what the *client* routes through the tunnel. Defaults to full-tunnel
  (`0.0.0.0/0, ::/0`); set to e.g. `10.10.0.0/24` for split-tunnel (VPN traffic only).
- `persistent_keepalive` — seconds between keepalive packets. Defaults to `25`, useful for peers
  behind NAT.

## Security note

Both `peers.json` (once real keys are generated) and everything under `out/` contain private keys.
Both are git-ignored by default — don't commit them.

## Running the tests

```sh
python -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
