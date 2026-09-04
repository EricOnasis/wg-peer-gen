# wg-peer-gen

Generate a WireGuard server config and matching per-peer client configs from a single peer list.
No `wg` binary required; key generation is pure Python (X25519 via `cryptography`, verified
byte-for-byte compatible with `wg genkey`/`wg pubkey`).

## Installation

```sh
pip install -r requirements.txt
```

## Usage

Copy the example peer list and edit it:

```sh
cp peers.example.json peers.json
```

Leave `private_key`/`public_key` as `null` — they're generated on first run and written back into
the file, so re-running is idempotent.

```sh
python generate.py peers.json --out ./out
```

This writes `out/server.conf` and one `out/clients/<name>.conf` per peer.

QR code generation for mobile clients coming soon.

## License

MIT — see [LICENSE](LICENSE).
