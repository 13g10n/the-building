# Terry

Exit node for the tailnet. Laptop traffic leaves through him, and he only steps outside through Nord.

CT 403 on ugly-naked-guy. Address `10.0.4.3/16` on `vmbr0`, gateway `10.0.0.1`. Debian, 1 core, 2 GB RAM, 8 GB on `local-lvm`. The CT is privileged. Headscale stays on [Gunther](../gunther/README.md) and does not run here.

## Host config

The Proxmox create form turns nesting off when Unprivileged is unchecked. Docker's overlay mount stays denied until nesting is set from the host and the CT is stopped and started there. A reboot inside the CT does not reload this file.

```bash
pct set 403 --features nesting=1
pct stop 403
pct start 403
```

`/etc/pve/lxc/403.conf` also needs the TUN device Gluetun uses:

```text
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```

On the CT, `/etc/docker/daemon.json`:

```json
{
  "storage-driver": "overlay2"
}
```

Docker 29's default containerd snapshotter mounts overlay with `index=off` and gets `permission denied` in this CT. `overlay2` gets the same error until nesting is loaded. `mount overlay` without `-t` looks up `/etc/fstab` and prints `can't find in /etc/fstab`. The check that actually calls the kernel is:

```bash
mkdir -p /tmp/ovl/{lower,upper,work,merged}
mount -t overlay -o lowerdir=/tmp/ovl/lower,upperdir=/tmp/ovl/upper,workdir=/tmp/ovl/work overlay /tmp/ovl/merged
```

Then `systemctl reset-failed docker && systemctl start docker`.

## Services

- [Gluetun](gluetun/README.md) is a new Nord OpenVPN tunnel. Tailscale runs inside that network namespace and advertises the exit node.

Gunther's Gluetun keeps serving the HTTP proxy on `10.0.4.4:8888`. Leave that container running. This stack publishes no proxy.
