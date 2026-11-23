# Richard

Keeps the household health chart: meals, workouts, and the rest of the record. Monica's ophthalmologist, the one who already looked after people and didn't make a fuss about it.

CT 207 on beige-carpet. Address `10.0.2.7/16` on `vmbr0`, gateway `10.0.0.1`. Debian 13, 1 core, 2 GB RAM, 16 GB on `yellow-frame`. Unprivileged.

SparkyFitness is the first service. The iPhone and the watch use `https://fitness.13g10n.dev`. Jack's Caddy proxies that name to `10.0.2.7:3004`. The name stays private. Jack's existing AdGuard wildcard already sends `*.13g10n.dev` to Caddy, and the wildcard certificate covers it. The phone reaches Caddy over Tailscale the same way it reaches Paperless.

## Host config

Docker in this CT needs nesting. Set it before the first start:

```bash
pct set 207 --features nesting=1,keyctl=1
```

Docker Engine and the Compose plugin on the CT. Install steps: <https://docs.docker.com/engine/install/debian/>

If Docker then fails to mount overlay, use the `overlay2` driver the same way [Terry](../../ugly-naked-guy/terry/README.md) does.

## Files

| Path | Role |
| --- | --- |
| `sparkyfitness/compose.yml` | Postgres, the API, and the web UI |
| `sparkyfitness/.env` | Secrets and the site URL. Not committed |

Postgres data, backups, and uploads are the `postgresql`, `backup`, and `uploads` directories next to the compose file. They are created on first start.

Images: `postgres:18.3-alpine`, `codewithcj/sparkyfitness_server:latest`, `codewithcj/sparkyfitness:latest`.

## Configure

Generate `.env` with the official generator: <https://codewithcj.github.io/SparkyFitness/install/env-generator>

Choose the custom-domain fill. Set the site URL to `https://fitness.13g10n.dev` with no port. Put the file next to `compose.yml`.

Compose will not start while the database password, the API encryption key, or the auth secret is missing. Diary days use `Europe/Minsk` unless `.env` sets `TZ`.

Behind this Caddy the trust count is 2: Caddy, then the frontend nginx. Compose uses 2 when `SPARKY_FITNESS_TRUSTED_PROXY_HOPS` is unset.

## Start

From `/opt/sparkyfitness` on the CT:

```bash
docker compose up -d
docker compose ps
```

The UI answers on `https://fitness.13g10n.dev` after Caddy is reloaded. From Jack's `caddy` directory:

```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

The first account to sign up is the administrator.
