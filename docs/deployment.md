# Deployment

Recommended with systemd:
- run in foreground and let systemd supervise
- set runtime/state dirs with env vars for non-root setups
- keep socket paths in `/run/marpelle` for root services
- use least-privilege service users
