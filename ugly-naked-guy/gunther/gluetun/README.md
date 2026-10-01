# Gluetun

NordVPN exit for Gunther. Headscale stays on the CT network and does not use this container. Tag sends Grok's API traffic through the HTTP proxy.

Image: `qmcgaw/gluetun` (unpinned). VPN type is OpenVPN over TCP. UDP 1194 from this network never finishes the TLS handshake, and every Lithuania endpoint timed out. The exit country is the United States, limited to standard Nord servers so a Dedicated IP host is not selected.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | Container, proxy port, VPN settings |
| `.env` | Nord service credentials, country, category, proxy login. Not committed |
| `gluetun/` | Server list and runtime data. Not committed |

## Configure

Create `.env` next to `compose.yml` on the CT before the first start.

| Variable | Example | Purpose |
| --- | --- | --- |
| `VPN_SERVICE_PROVIDER` | `nordvpn` | Provider |
| `OPENVPN_USER` | service username | Nord service credential, not the account email |
| `OPENVPN_PASSWORD` | service password | Nord service credential |
| `SERVER_COUNTRIES` | `United States` | Exit country |
| `SERVER_CATEGORIES` | `Standard VPN servers` | Keeps Dedicated IP hosts out of the pool |
| `HTTPPROXY_USER` | `grok` | Login for the HTTP proxy |
| `HTTPPROXY_PASSWORD` | long random string | Login for the HTTP proxy |
| `TZ` | `Europe/Minsk` | Container timezone |

`OPENVPN_PROTOCOL=tcp` is set in `compose.yml`. The proxy listens inside the container on `:8888` and is published only on `10.0.4.4:8888`.

## Start

```bash
docker compose up -d
docker compose logs -f gluetun
```

The log line `Initialization Sequence Completed` means the tunnel is up. A healthy container is the proxy you can use.

From Tag:

```bash
curl -fsS --max-time 25 -x http://10.0.4.4:8888 https://ipinfo.io/country
```

That request has no proxy login, so the proxy answers `407`. With the login from `.env`, the same URL returns `US`.

## Grok

Tag's `orca` user keeps the proxy URL in `/home/orca/.config/grok-proxy.env` (mode `600`, not in git). The `grok` and `agent` commands on that account are wrappers that load the file and then run the real binary. A later `grok update` may replace those wrappers with symlinks; put the wrapper in [tag/orca/grok](../../tag/orca/grok) back in place if that happens.
