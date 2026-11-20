# Doug

Metrics for the building. Chandler's boss wants every number on a chart and gets loud when a line moves.

This directory runs Grafana and Loki. Loki stores logs. Grafana is the UI. Prometheus and the exporters are later.

Image pins: `grafana/loki:3.7.10`, `grafana/grafana:13.3.1`.

## Files

| Path | Role |
| --- | --- |
| `compose.yml` | Loki and Grafana |
| `loki-config.yaml` | Retention, filesystem storage, single-binary ring |
| `grafana/provisioning/datasources/loki.yaml` | Loki datasource inside Grafana |
| `.env` | Grafana admin login. Not committed |

Loki chunks and the Grafana database are Docker volumes (`loki-data`, `grafana-data`), created on the CT at first start.

## Configure

On the CT, create `.env` in this directory before the first start. Compose reads it for the values below. It is not copied into the container as a file.

| Variable | Example | Purpose |
| --- | --- | --- |
| `GF_SECURITY_ADMIN_USER` | `admin` | Grafana admin user. Defaults to `admin` when omitted |
| `GF_SECURITY_ADMIN_PASSWORD` |  | Grafana admin password. Required |
| `TZ` | `Europe/Minsk` | Container timezone. Defaults to `Europe/Minsk` when omitted |

Quote a value that contains a space or `#`.

The admin password is stored in Grafana's database on first start. A later edit of `.env` does not change it. To set a new one, reset it from a shell in the Grafana container, or remove the `grafana-data` volume and start again.

## Start

Docker Engine and the Compose plugin on the CT. Install steps: <https://docs.docker.com/engine/install/debian/>

```bash
docker compose up -d
docker compose ps
```

Loki is up when this prints `ready`:

```bash
curl -fsS http://127.0.0.1:3100/ready
```

Grafana is `http://<doug>:3000`. The Loki datasource is already provisioned. Open Explore, choose Loki, and run a query once another host is shipping logs.

Port 3100 is the push API. It has no login. Leave it on the homelab LAN. Do not publish it through Caddy or Cloudflare.

This stack keeps its own container logs in Docker's json-file driver. Do not point those two containers at this Loki with the logging driver below. A Loki that cannot finish starting because it is waiting to ship its own logs is a loop.

## Retention

Logs are kept for 60 days (`1440h` in `loki-config.yaml`, both `retention_period` and `max_query_lookback`). The compactor deletes older chunks. A change applies to logs ingested after the restart. Recreate Loki after editing the file:

```bash
docker compose up -d loki
```

## Send logs from another machine

Do this on the Docker host that runs the other Compose stack. The plugin is a Docker logging driver on that host. It is not a container, and it is not installed on Doug.

The host needs to reach `http://<doug>:3100`. Check that before changing a stack:

```bash
curl -fsS http://<doug>:3100/ready
```

Install the driver once. The tag is the one in the current Loki docker-driver docs. An arm64 host uses `3.7.0-arm64` instead of `3.7.0-amd64`.

```bash
docker plugin install grafana/loki-docker-driver:3.7.0-amd64 --alias loki --grant-all-permissions
docker plugin ls
```

`loki` should show `true` under enabled.

Add this to one service in that stack's `compose.yml`. Replace `<doug>` with this CT's address, and keep the service's existing keys.

```yaml
    logging:
      driver: loki
      options:
        loki-url: "http://<doug>:3100/loki/api/v1/push"
        loki-retries: "2"
        loki-max-backoff: "800ms"
        loki-timeout: "1s"
        keep-file: "true"
        max-size: "10m"
        max-file: "3"
        mode: "non-blocking"
        max-buffer-size: "4m"
```

`mode: non-blocking` keeps the container running when Doug is down. The driver then buffers about 4 MB and drops what does not fit. `loki-retries`, `loki-max-backoff`, and `loki-timeout` stop the Docker daemon from waiting on a dead Loki. `keep-file` leaves a local json log so `docker compose logs` still works. `max-size` and `max-file` bound that file.

Every option value is a string. Compose will reject an unquoted `2` or `true`.

Recreate the service so Docker loads the driver. A restart keeps the old driver.

```bash
docker compose up -d
```

If the plugin is missing, that command fails with `error looking up logging plugin loki`.

The driver adds `compose_project`, `compose_service`, `host`, `filename`, and `container_name`. In Grafana Explore:

```logql
{compose_service="<service>", host="<hostname>"}
```

`<service>` is the Compose service name. `<hostname>` is the Docker host's hostname. A line from that container means the path works. Add the same `logging` block to the other services in the stack when it does.
