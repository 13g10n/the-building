# Primary AdGuard Home

Jack is the origin. `adguardhome-sync` copies this instance onto Judy (`10.0.3.5`) every 10 minutes, and again at startup. A change made on Judy is replaced on the next run. Edit filters, rewrites, clients, and DNS settings here.

AdGuard's own settings stay in the UI. The container writes them under `conf/`. The sync file only says where to copy them and which parts to copy. It reads Jack through the API at `http://adguard:80`.

Image pin: `ghcr.io/bakito/adguardhome-sync:v0.9.6`.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | AdGuard and the sync container |
| `adguardhome-sync.yaml` | Schedule, Judy's URL, and which settings are copied |
| `.env` | Admin logins for both UIs. Not committed |
| `conf/` | AdGuard's config, written by the container. On the CT |
| `data/` | Query log and statistics. On the CT. Each host keeps its own |

## Secrets

Create `.env` in this directory on Jack before the first start. These are the existing AdGuard admin logins. Both UIs have to be past the setup wizard already.

| Variable | Purpose |
| --- | --- |
| `ORIGIN_USERNAME` | Jack's AdGuard admin user |
| `ORIGIN_PASSWORD` | Jack's AdGuard admin password |
| `REPLICA1_USERNAME` | Judy's AdGuard admin user |
| `REPLICA1_PASSWORD` | Judy's AdGuard admin password |

Quote a value that contains a space or `#`.

## Start

```bash
docker compose up -d
docker compose logs -f adguardhome-sync
```

A successful run logs a sync from Jack to `10.0.3.5:8080`. On the CT:

```bash
curl -fsS http://127.0.0.1:8081/readyz
```

That address is the sync status page, bound to loopback. AdGuard's UI stays on port 8080.

DHCP settings are left out. TLS settings are left out. Query logs and statistics stay on each host. The copy includes rewrites, filters, user rules, blocked services, clients, and DNS settings.

## Rewrite rules

```
||*.13g10n.dev^$dnsrewrite=10.0.2.5,denyallow=hs.13g10n.dev
```
