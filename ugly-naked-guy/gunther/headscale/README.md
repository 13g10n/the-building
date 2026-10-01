# Headscale

Self-hosted Tailscale control server for Gunther. Nodes still run the official Tailscale client and move traffic peer to peer over WireGuard. This container only coordinates them.

Image pin: `docker.io/headscale/headscale:0.29.4`. Minimum Tailscale client: 1.80.0.

Gluetun on this CT is a separate Compose project. Leave Headscale off that network. The control server has to answer on the public address, not through the VPN exit.

## Resources

2 CPU and 2 GB is enough. Headscale is a control plane: idle use is tens of megabytes, and SQLite replaces a database server. WireGuard traffic does not pass through this container unless you later enable the embedded DERP relay. Gluetun is the heavier process on this CT, and 2 GB still covers both for a homelab tailnet. Increase RAM only if you add more services to the CT.

## Requirements

- Docker Engine and the Compose plugin on the Debian 13 CT. Install steps: <https://docs.docker.com/engine/install/debian/>
- A DNS name with an A record pointed at your public IPv4. Add an AAAA record only when this CT accepts IPv6 on port 443.
- Router port forward: TCP 443 to this CT's port 443.
- Outbound HTTPS, so Let's Encrypt and the public DERP map can be reached.

Do not forward TCP 9090. Metrics are published on the CT loopback only (`127.0.0.1:9090`).

Clients on the same LAN as the router can fail to reach the public address when the router has no NAT loopback. Register the first node from a network outside the house, or add a local DNS record for the hostname that points at the CT.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | Container, ports, volume mounts |
| `config.yaml` | Headscale settings that are not specific to this site |
| `.env` | Hostname, server URL, ACME email, MagicDNS suffix. Not committed |
| `data/` | SQLite database, Noise private key, Let's Encrypt account and certificates. Not committed |

`.env` is ignored by the repo `.gitignore`. `data/` is ignored here because it holds the Noise key and the certificate account.

## Configure

On the CT, create `.env` in this directory before the first start. The variables are in the table below. Changing `HEADSCALE_SERVER_URL` or `HEADSCALE_DNS_BASE_DOMAIN` after nodes have joined means rejoining them.

`HEADSCALE_TLS_LETSENCRYPT_HOSTNAME` is the name in the certificate. `HEADSCALE_SERVER_URL` is that same name with `https://` and no port. Headscale refuses to start when the MagicDNS suffix is the server hostname or a parent of it, because clients would capture DNS for the control server itself.

| Variable | Example | Purpose |
| --- | --- | --- |
| `TZ` | `Europe/Minsk` | Container timezone |
| `HEADSCALE_TLS_LETSENCRYPT_HOSTNAME` | `hs.example.com` | Certificate name |
| `HEADSCALE_SERVER_URL` | `https://hs.example.com` | URL clients dial |
| `HEADSCALE_ACME_EMAIL` | `contact@13g10n.com` | Let's Encrypt account contact |
| `HEADSCALE_DNS_BASE_DOMAIN` | `tailnet.internal` | MagicDNS suffix |

`tailnet.internal` does not need a public DNS record. A node named `laptop` is then `laptop.tailnet.internal` inside the tailnet.

TLS uses the built-in Let's Encrypt client with the TLS-ALPN-01 challenge, so only port 443 is required. Certificates are stored under `data/cache` and renew on their own.

DNS resolvers pushed to clients are in `config.yaml` under `dns.nameservers.global`. An empty policy path is allow-all. To restrict traffic, set `policy.path` to a HuJSON file mounted into the container and restart.

## Start

```bash
docker compose up -d
docker compose logs -f headscale
```

The first lines must show your real server URL. `headscale.invalid` means `.env` was not applied. Stop and fix that before any node joins.

From another network:

```bash
curl -fsS https://hs.example.com/health
```

`https://hs.example.com` is the value of `HEADSCALE_SERVER_URL`. A certificate warning means ACME has not finished. Check that port 443 reaches this CT and that the hostname resolves to the public address.

## Register a node

Create a user once. The name must not end with `@`.

```bash
docker compose exec headscale headscale users create alice
```

Pre-auth key (one use, one hour, printed once):

```bash
docker compose exec headscale headscale preauthkeys create --user alice
```

On the device, with the Tailscale client installed:

```bash
tailscale up --login-server https://hs.example.com --authkey <key>
```

Or register in a browser. On the device:

```bash
tailscale up --login-server https://hs.example.com
```

The page prints an auth id. On the CT:

```bash
docker compose exec headscale headscale auth register --user alice --auth-id <auth-id>
```

List what joined:

```bash
docker compose exec headscale headscale nodes list
docker compose exec headscale headscale users list
```

Approve advertised routes, such as a subnet router, with `headscale nodes approve-routes`. Run `headscale --help` inside the container for the rest of the CLI.

## Backup

Copy `data/` while the container is stopped, or use a SQLite-safe copy of `db.sqlite`. The Noise private key is `data/noise_private.key`. Losing it forces every node to log in again. Losing `data/cache` only forces a new Let's Encrypt certificate.

## Embedded DERP

Leave this off unless direct connections fail and you want the relay on your own address. Relayed packets are still WireGuard-encrypted either way. Public DERP is the fallback used now.

To relay here, set `derp.server.enabled: true`, set `derp.server.ipv4` to the public IPv4 (and `ipv6` if you have one), keep `derp.server.stun_listen_addr: "0.0.0.0:3478"`, publish `3478:3478/udp`, and forward UDP 3478 on the router. Restart Headscale. `server_url` must stay `https`.

## Upgrade

Read <https://headscale.net/stable/setup/upgrade/> before changing the image tag. Move one stable minor release at a time, and back up `data/` first. Keep `config.yaml` aligned with the example for that tag.
