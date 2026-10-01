# Gunther

The quiet, ever-present manager who sees and controls all the traffic. He runs the tailnet control server, plus the VPN exit and HTTP proxy — the gateway everything has to pass through, always watching, slightly judgmental, and ensuring nothing gets in or out without going through him first.

## Services

- [Headscale](headscale/README.md) runs the Tailscale control server.
- [Gluetun](gluetun/compose.yml) is the VPN exit and HTTP proxy.
