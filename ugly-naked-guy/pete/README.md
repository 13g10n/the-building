# Pete

The software billionaire with serious resources and zero restrictions. He runs the powerful, unrestricted Computer CT — the one built for real work, deep tasks, and full system access.

## Initial setup and updates

Pete runs cptr at system level.

Install via `uv`:
```bash
uv tool install 'cptr[all]'
```

To run in background with auto-restarts, create `/etc/systemd/system/cptr.service`

```bash
systemctl daemon-reload
systemctl enable --now cptr
systemctl restart cptr
```

Updates available via `uv`:
```bash
uv tool upgrade cptr
systemctl restart cptr
```
