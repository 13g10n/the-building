# Orca

Headless Orca runtime on Tag. Agents, git worktrees, and terminals stay here. The MacBook pairs over the tailnet and is only the UI.

Orca `1.4.217` is the extracted AppImage at `/opt/orca/squashfs-root`. The version is recorded in `/opt/orca/VERSION`. The Mac app in use is `1.4.218`.

## Layout on the CT

| Path | Role |
| --- | --- |
| `/opt/orca/squashfs-root/AppRun` | Server binary. Root-owned, world-executable |
| `/usr/local/sbin/orca-serve` | Waits for a Tailscale IPv4, then starts `orca serve` |
| `/etc/systemd/system/orca-serve.service` | Runs that script as user `orca` |
| `/home/orca` | Service home. Linger is enabled |
| `/home/orca/code` | Directory for repositories |
| `/home/orca/.config/grok-proxy.env` | Proxy URL for Grok. Mode `600`. Not committed |
| `/home/orca/.grok/downloads/grok-linux-x86_64` | Grok `1.0.46` |

The service user is `orca` (uid 999, shell `/bin/bash`). Electron is not run as root. `ELECTRON_DISABLE_SANDBOX=1` is set because this unprivileged LXC has no usable Chromium sandbox. `DISPLAY` is unset so Orca starts its own Xvfb. `loginctl enable-linger orca` is already done, so agent terminals can outlive a service restart.

There is no GNOME keyring in the CT, so Orca stores its secrets as files under `/home/orca`.

## Tailscale

Tag is a node on the Headscale tailnet at `https://hs.13g10n.dev`, user `13g10n`, hostname `tag`. The address it has now is `100.64.0.3`.

This CT cannot create `/dev/net/tun`, so `tailscaled` is started with `--tun=userspace-networking` (`FLAGS` in `/etc/default/tailscaled`). Clients still reach the node. The MacBook's path to `100.64.0.3:6768` arrives at `tailscaled`, which connects to `127.0.0.1:6768`.

`orca` is a Tailscale operator, so the service can read `tailscale ip -4`.

Join command, with a pre-auth key created on Gunther for user id `1`:

```bash
tailscale up --login-server=https://hs.13g10n.dev --auth-key=<key> \
  --hostname=tag --accept-dns=true --accept-routes=false --ssh=false
```

## Firewall

`ufw` is active. Incoming policy is deny.

| Rule | Why |
| --- | --- |
| OpenSSH | Administration on the LAN |
| UDP `41641` | Tailscale userspace packets |
| TCP `6768` from `127.0.0.1` | The userspace forward onto Orca |

Port `6768` is bound on `0.0.0.0`. The firewall is what keeps the LAN off it. A connection to `10.0.4.5:6768` does not complete. A connection to `100.64.0.3:6768` succeeds.

## Service

```bash
systemctl enable --now orca-serve.service
journalctl -u orca-serve.service -o cat
```

A ready server prints one JSON line with `"type":"orca_server_ready"`. The pairing URL in that line is a credential. It is not stored in this repo. Copy it from the journal when pairing a new client:

```bash
journalctl -u orca-serve.service -o cat | jq -Rrc 'fromjson? | select(.type=="orca_server_ready") | .pairing.url'
```

On the Mac, with Tailscale already pointed at `https://hs.13g10n.dev`:

1. Open Orca and choose **Settings → Remote Orca Servers → Add Server**.
2. Paste the `orca://pair?...` URL.
3. Set this runtime as the active server when new work should live on Tag.
4. **Settings → Agents → Agent Permissions → Yolo** is stored on this runtime.

`orca account add` on this build manages Claude and Codex only. Grok is the CLI on `PATH`.

## Grok

Grok `1.0.46` is installed for `orca`. Direct egress from Tag is `BY`. Grok's traffic goes through Gunther's Gluetun proxy and leaves from a US address. The proxy login lives only in `/home/orca/.config/grok-proxy.env`.

The wrappers at these paths are the script in `grok`:

- `/home/orca/.local/bin/grok`
- `/home/orca/.local/bin/agent`
- `/home/orca/.grok/bin/grok`
- `/home/orca/.grok/bin/agent`

Sign in from the CT. Device auth prints a code to finish in a browser:

```bash
sudo -u orca -H grok login --device-auth
```

`grok update` can replace the wrappers with symlinks to the raw binary. Copy `grok` back over those four paths after an update so the proxy stays in front.

## Upgrade

Replace `/opt/orca/orca-linux.AppImage`, extract it again, `chmod -R a+rX /opt/orca/squashfs-root`, write the new version to `/opt/orca/VERSION`, and restart `orca-serve.service`. State stays in `/home/orca/.config`. Upstream detail: [Headless Linux Server](https://github.com/stablyai/orca/blob/main/docs/reference/headless-linux-server.md).
