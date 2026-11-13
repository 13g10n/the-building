# Hall closet

Storage node. The closet disk is mounted on the host and bind-mounted into containers.

## Disks

| Mount | Device | Size |
| --- | --- | --- |
| `/mnt/pve/closet` | `/dev/disk/by-uuid/5496704d-f2da-4064-b50e-e5586e02b98f` | 480 GB |

ext4, mounted by Proxmox at `/mnt/pve/closet`. Add Storage is off, so it stays off the datacenter storage list.

The directory is `100000:100000`. Root in an unprivileged CT can write. If writes return permission denied:

```bash
chown 100000:100000 /mnt/pve/closet
```

Run that on the node. The same command inside a CT cannot change the owner.

## Mount into a CT

`pct set` can run while the CT is up. The mount appears after a reboot. Use the next free `mpN`.

```bash
pct set <id> -mp0 /mnt/pve/closet,mp=/srv/closet,backup=0
pct reboot <id>
```

The path inside the CT can differ. Treeger (CT 502) already has this mount at `/srv/closet`.

Another unprivileged CT on hall-closet can use the same host path. Both see the same files. A CT on another node cannot use this disk.
