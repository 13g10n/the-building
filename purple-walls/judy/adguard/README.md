# Secondary AdGuard Home

Judy receives a copy of Jack's AdGuard settings. The sync container runs on Jack and pushes that copy every 10 minutes. Change filters, rewrites, clients, and DNS settings on Jack. Judy's compose file stays as it is.

Her admin login is `REPLICA1_USERNAME` and `REPLICA1_PASSWORD` in Jack's `.env`. The UI on this host has to be past the setup wizard before the first sync.

## Rewrite rules

Jack copies this rule here:

```
||*.13g10n.dev^$dnsrewrite=10.0.2.5,denyallow=hs.13g10n.dev
```
