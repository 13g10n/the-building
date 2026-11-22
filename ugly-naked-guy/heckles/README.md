# Heckles

Push notifications for the building. He lives downstairs and bangs on the ceiling the moment anything happens upstairs.

CT 405 on ugly-naked-guy. Address `10.0.4.5/16` on `vmbr0`, gateway `10.0.0.1`. Debian, 1 core, 1 GB RAM, 8 GB on `local-lvm`. Unprivileged. The ntfy process sits around 15 MB. The 1 GB is for Debian and Docker.

Image pin: `binwiederhier/ntfy:v2.38.1`.

The server listens on `http://10.0.4.5`. Phones and browsers use `https://ntfy.13g10n.dev`, which Jack's Caddy proxies to that address. Anonymous access is denied. The public name is safe only because every publish and subscribe needs an account or a token.

## Host config

Docker in this CT needs nesting. Set it before the first start:

```bash
pct set 405 --features nesting=1,keyctl=1
```

Docker Engine and the Compose plugin on the CT. Install steps: <https://docs.docker.com/engine/install/debian/>

If Docker then fails to mount overlay, use the `overlay2` driver the same way [Terry](../terry/README.md) does.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | ntfy |
| `.env` | Timezone and the Web Push keypair. Not committed |

The message cache, user database, attachment cache, and Web Push subscriptions are the Docker volume `ntfy-data`.

## Web Push keys

These two variables are the VAPID keypair for browser background notifications (Safari on the Mac, and the web app). The iPhone app does not use them. It is woken through `ntfy.sh` and then downloads the message from this server.

Generate the pair before the first start. Compose refuses to start while either variable is missing, so this uses a one-off container rather than `docker compose exec`.

```bash
docker run --rm binwiederhier/ntfy:v2.38.1 webpush keys
```

The command prints two lines:

```text
web-push-public-key: <public key>
web-push-private-key: <private key>
```

Write them into `.env` next to `compose.yml` under the names Compose expects:

```text
TZ=Europe/Minsk
NTFY_WEB_PUSH_PUBLIC_KEY=<public key>
NTFY_WEB_PUSH_PRIVATE_KEY=<private key>
```

Leave the values unquoted. They are base64url and contain none of the characters Compose treats specially.

Keep this pair. Browsers bind notification permission to the public key. A new pair means each browser has to have its notification permission cleared and turned on again, and open web apps miss pushes until that happens.

## Start

```bash
docker compose up -d
docker compose ps
```

ntfy is up when this prints `"healthy":true`:

```bash
curl -fsS http://10.0.4.5/v1/health
```

## Accounts

Signup is off. Create accounts from the CT. `me` is the account the iPhone logs in as. `pve` and `pbs` only publish.

```bash
docker compose exec ntfy ntfy user add me
docker compose exec ntfy ntfy access me proxmox read-write
docker compose exec ntfy ntfy access me pbs read-write
docker compose exec ntfy ntfy access me building read-write

docker compose exec ntfy ntfy user add pve
docker compose exec ntfy ntfy access pve proxmox write
docker compose exec ntfy ntfy token add pve

docker compose exec ntfy ntfy user add pbs
docker compose exec ntfy ntfy access pbs pbs write
docker compose exec ntfy ntfy token add pbs
```

`user add` asks for a password. `token add` prints a `tk_...` token once. Store each token where that Proxmox host keeps notification secrets. A write token can publish to its one topic and cannot read the others.

Check a publish from the CT. Use the `pve` token:

```bash
curl -fsS \
  -H "Authorization: Bearer tk_..." \
  -H "Title: Heckles" \
  -d "Downstairs is listening." \
  http://10.0.4.5/proxmox
```

## Caddy and the public name

`ntfy.13g10n.dev` is a handle in Jack's Caddy. At home, Jack's AdGuard wildcard already sends `*.13g10n.dev` to Caddy, so no DNS rewrite is required.

Reload Caddy after copying the new Caddyfile onto Jack:

```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Run that in Jack's `caddy` directory.

Away from home, and while NordVPN is up, the phone does not use Jack's DNS. Add a public hostname `ntfy.13g10n.dev` on the Cloudflare tunnel that already publishes `h.`, with the same service URL. The iPhone downloads the message body from this name after Apple wakes it. Without the public name, a locked phone shows "New message" and fills in the body the next time it can reach the server.

## iPhone

Install **ntfy** from the App Store (the app by Philipp C. Heckel).

1. Open Settings with the cog at the bottom.
2. Set the default server to `https://ntfy.13g10n.dev`.
3. Add the user `me` and the password from `ntfy user add`.
4. Allow notifications when iOS asks.
5. Subscribe to `proxmox`, `pbs`, and `building`.

Instant delivery is already turned on in `compose.yml` (`NTFY_UPSTREAM_BASE_URL`). The phone still has to reach `https://ntfy.13g10n.dev` to fetch the text. Send the curl publish above with the phone locked and on cellular, and confirm the title and body both arrive.

## Proxmox VE and Proxmox Backup Server

Both take the same Webhook target. PVE is under **Datacenter → Notifications**. PBS is under **Configuration → Notifications**. Create one target on each server. Put the token in the target's secret list, not in the URL.

| Field | PVE | PBS |
| --- | --- | --- |
| Name | `heckles` | `heckles` |
| Method | POST | POST |
| URL | `http://10.0.4.5/proxmox` | `http://10.0.4.5/pbs` |
| Header `Authorization` | `Bearer {{ secrets.token }}` | `Bearer {{ secrets.token }}` |
| Header `Title` | `{{ title }}` | `{{ title }}` |
| Header `Markdown` | `Yes` | `Yes` |
| Body | `{{ message }}` | `{{ message }}` |
| Secret `token` | the `pve` token | the `pbs` token |

On the matcher that should page you, add target `heckles`. The test button on the target posts one notification. A successful backup and a failed job both arrive until the matcher filters on severity.

LAN posts stay on `10.0.4.5`, so an alert still sends when the tunnel is down.
