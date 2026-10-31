# Chandler

Proxmox VM 203 at `10.0.2.3`. Debian 13. SSH as `admin`; root is `su`. `admin` has no `sudo` binary.

- [a-borisenko.com](a-borisenko/README.md)
- [tax-json.a-borisenko.com](a-borisenko.nalog/README.md)

## GitHub Actions runner

The self-hosted runner is `/opt/actions-runner`, owned by `admin`. `config.sh` must already have succeeded as `admin`. That is what creates `svc.sh`.

Stop a foreground `./run.sh` before installing the service. One registration has one listener.

`su` does not set `SUDO_USER`. Pass `admin` or `svc.sh` installs the unit as root. From `/opt/actions-runner`, as root:

```bash
./svc.sh install admin
./svc.sh start
./svc.sh status
```

`install` enables the unit and copies `bin/runsvc.sh` to `/opt/actions-runner/runsvc.sh`, owned by `admin`. The unit name is stored in `/opt/actions-runner/.service`. Shape: `actions.runner.<owner-or-org>.<runner>.service`.

The unit `svc.sh` writes:

```ini
[Unit]
Description=GitHub Actions Runner (<scope>.<name>)
After=network-online.target

[Service]
ExecStart=/opt/actions-runner/runsvc.sh
User=admin
WorkingDirectory=/opt/actions-runner
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min

[Install]
WantedBy=multi-user.target
```

`runsvc.sh` is the entry point. It runs `bin/RunnerService.js`, which supervises `Runner.Listener`. Leave `KillMode=process`. Leave the unit without `Restart=`.

`admin` is in the `docker` group. systemd keeps supplementary groups, so jobs can use the Docker socket.

Debian's `needrestart` restarts services after library upgrades. Ignore runner units so an upgrade does not kill a job:

```bash
install -d /etc/needrestart/conf.d
printf '%s\n' '$nrconf{override_rc}{qr(^actions\.runner\..+\.service$)} = 0;' \
  > /etc/needrestart/conf.d/actions_runner_services.conf
```

Status and logs:

```bash
systemctl is-active "$(cat /opt/actions-runner/.service)"
journalctl -u "$(cat /opt/actions-runner/.service)" -n 50 --no-pager
```

Runner logs are also under `/opt/actions-runner/_diag`. Job checkouts are `/opt/actions-runner/_work`. Both are on the 32G root.

If the tree is not `admin:admin`:

```bash
chown -R admin:admin /opt/actions-runner
```
