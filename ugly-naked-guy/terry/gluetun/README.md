# Gluetun

NordVPN exit for Terry, with Tailscale in the same network namespace. Forwarded tailnet traffic leaves through Nord. Headscale on Gunther is the control server at `https://hs.13g10n.dev`.

Gluetun owns `/dev/net/tun`, so Tailscale runs userspace (`TS_USERSPACE=true`) and shares Gluetun's namespace (`network_mode: service:gluetun`). Peers see the Nord address, so the usual path is a DERP relay. The first test checks the exit address. `FIREWALL_OUTBOUND_SUBNETS` lets the tailnet (`100.64.0.0/10`) and the whole homelab (`10.0.0.0/16`) out of the Nord tunnel.

With the exit node selected, the Mac sends DNS to Terry. Headscale 0.29 does not emit "use with exit node", so its global nameserver list is not used in that mode. Gluetun forwards in plaintext to AdGuard on Jack (`10.0.2.5`) and Judy (`10.0.3.5`). `*.13g10n.dev` is exempt from Gluetun's DNS rebinding protection, because Jack answers those names with `10.0.2.5` and Gluetun otherwise returns `SERVFAIL`. Gluetun's own blocklists are off. Recreate the stack after changing this. AdGuard's query log shows Terry's address, `10.0.4.3`.

That covers every client that has the exit node selected, at home and away. A client with Tailscale up and no exit node still uses Headscale's global resolvers. Those are Cloudflare in `config.yaml`. Pointing them at `10.0.2.5` only works away from home if some other node, not Gunther and not this container, advertises `10.0.2.5/32` and `10.0.3.5/32`.

The image that registered was `tailscale/tailscale:stable` at v1.104.7. The Mac client that logged in was 1.102.4. Headscale 0.29.7 accepts clients from 1.80.0. macOS lists the exit node when Headscale is 0.29.5 or newer, because that is when it sends `suggest-exit-node`. Gunther's compose file in git still pins 0.29.4. Confirm the running server with `headscale version` on Gunther.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | Gluetun plus the Tailscale exit |
| `.env` | Nord service credentials, server choice, timezone, one-time Tailscale auth key. Not committed |
| `tailscale-state/` | Node state, including the machine key. Not committed |
| `gluetun/` | Server list and runtime data. Not committed |

The stack on the CT is `~/gluetun` as root. Copy `compose.yml` there. Leave `.env` and `tailscale-state/` on the CT.

## Configure

Create `.env` next to `compose.yml` before the first start.

| Variable | Example | Purpose |
| --- | --- | --- |
| `VPN_SERVICE_PROVIDER` | `nordvpn` | Provider |
| `OPENVPN_USER` | service username | Nord service credential, not the account email |
| `OPENVPN_PASSWORD` | service password | Nord service credential |
| `OPENVPN_PROTOCOL` | `udp` | Protocol Gunther is actually using |
| `SERVER_COUNTRIES` | `Lithuania` | Exit country |
| `SERVER_CATEGORIES` | `Standard VPN servers` | Keeps Dedicated IP hosts out of the pool |
| `TZ` | `Europe/Minsk` | Container timezone |
| `TS_AUTHKEY` | one-time pre-auth key | First registration only. `TS_AUTH_ONCE=true` ignores it after that |

Read the provider, protocol, and category from Gunther's running container. Gunther's git compose still says TCP and a proxy login, and those values are stale. Keep `SERVER_COUNTRIES=Lithuania` on Terry.

```bash
docker inspect gluetun --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E '^(VPN_SERVICE_PROVIDER|VPN_TYPE|OPENVPN_PROTOCOL|SERVER_COUNTRIES|SERVER_CATEGORIES)='
```

Copy `OPENVPN_USER` and `OPENVPN_PASSWORD` from `/home/admin/gluetun/.env` on Gunther. Do not print them and do not commit `.env`.

Mint the Tailscale key on Gunther, from `/home/admin/headscale`. `--user` is the numeric id from `users list`. The name `13g10n` fails with `strconv.ParseUint`.

```bash
docker compose exec headscale headscale users list
docker compose exec headscale headscale preauthkeys create --user <id>
```

The default key is one use and one hour. Put it in `TS_AUTHKEY` and start before it expires.

## Start

```bash
docker compose up -d
docker compose logs -f gluetun
docker compose logs -f tailscale
```

Gluetun is up at `Initialization Sequence Completed`. Tailscale is up when the log says the node is registered and `Startup complete`.

`depends_on` does not wait for the tunnel. The first `tailscale up` can hit `context deadline exceeded` because Gluetun installs the default route mid-login. A restart finishes it:

```bash
docker compose restart tailscale
```

If the one-time key was spent and the container stays logged out, mint a new key, then:

```bash
docker compose down
rm -rf tailscale-state
docker compose up -d
```

Status from inside the container. The default socket is a stale symlink, so a plain `tailscale status` prints `Logged out` while the daemon is running. The log names the socket to use.

```bash
docker compose exec tailscale tailscale --socket=/tmp/tailscaled.sock status
```

## Approve the exit

On Gunther, from `/home/admin/headscale`. `approve-routes` replaces the node's whole approved list. Approving `0.0.0.0/0` also approves `::/0`.

```bash
docker compose exec headscale headscale nodes list-routes
docker compose exec headscale headscale nodes approve-routes --identifier <id> --routes 0.0.0.0/0
```

`<id>` is the live Terry node. If pages hang after the Mac selects the exit, check with `curl -4`. An approved `::/0` through this Gluetun can blackhole IPv6.

## Name

`TS_HOSTNAME=exit` is the name the client reports. Headscale stores a separate GivenName, and that is the name in `tailscale status`. A leftover node already named `exit` makes the new one `exit-1`. Changing the hostname in the container does not rename it.

```bash
docker compose exec headscale headscale nodes list
docker compose exec headscale headscale nodes delete --identifier <id-of-offline-exit>
docker compose exec headscale headscale nodes rename --identifier <id-of-live-node> exit
```

Delete the offline registration that holds `exit`. Leave the online node, and leave the Mac node.

## Mac

Jack's AdGuard rewrite `*.13g10n.dev` → `10.0.2.5` also answers `hs.13g10n.dev`. That address is Caddy, and `https://hs.13g10n.dev/key` is HTTP 200 with an empty body. Tailscale then fails login and logout with `unexpected end of JSON input` and `key hex has the wrong size, got 0 want 64`.

The DNS rewrites page cannot exclude one name. Delete that wildcard there and use a custom filtering rule:

```text
||*.13g10n.dev^$dnsrewrite=10.0.2.5,denyallow=hs.13g10n.dev
```

Other names such as `papers.13g10n.dev` stay on `10.0.2.5`. `hs.13g10n.dev` stays the public A record `217.21.60.143`, DNS-only in Cloudflare. Jack's sync copies this rule to Judy.

```bash
dig +short hs.13g10n.dev @10.0.2.5
curl -fsS https://hs.13g10n.dev/key
```

`dig` prints `217.21.60.143`. `curl` prints JSON with `publicKey`. Flush the Mac cache, then log in:

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
tailscale login --login-server=https://hs.13g10n.dev
```

Quit Nord on the Mac first. Its kill switch drops Tailscale even when both apps are installed.

Select the exit. `--exit-node-allow-lan-access` keeps the laptop's LAN. This stack does not advertise `10.0.0.0/8`, so lab addresses work from the laptop only while it is on that LAN.

```bash
tailscale set --exit-node=exit --exit-node-allow-lan-access=true
curl -4 https://ipinfo.io
```

The address is a Nord address. `217.21.60.143` means the exit is not in use. Turn it off with:

```bash
tailscale set --exit-node=
```

Use the GivenName from `tailscale status` when the node is still `exit-1`.
