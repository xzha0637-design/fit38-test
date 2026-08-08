# Aliyun ECS deployment

This directory records the configuration used for the restricted-access
demonstration deployment on `8.218.145.76`.

## Runtime layout

- application release: `/opt/fit5238-signal-review/releases/0f20643`;
- active release link: `/opt/fit5238-signal-review/current`;
- Python environment: `current/.venv` (Python 3.10);
- SQLite state: `/var/lib/fit5238/feedback.sqlite3`;
- service environment: `/etc/fit5238/signal-review.env`;
- systemd unit: `/etc/systemd/system/fit5238.service`;
- Nginx site: `/etc/nginx/sites-available/fit5238-signal-review`.

The application runs as the non-login `fit5238` user, binds only to
`127.0.0.1:8000`, and uses one Uvicorn worker because pending assessment
context is process-local. Nginx is the only public listener.

## Access boundary

The current HTTP demonstration is publicly reachable through Nginx on port 80.
Port 8000 must remain closed because Uvicorn binds only to loopback. Nginx applies
separate limits to scoring, batch and analyst-workflow requests, and public
feedback export is disabled.

`X-Project-Role` is a demonstration role header, not real authentication. A
public deployment still requires a domain, trusted HTTPS and real authentication
(or HTTPS-protected Basic Auth) before it can be considered production-ready.

## Operations

```bash
systemctl status fit5238 nginx
journalctl -u fit5238 --no-pager -n 100
nginx -t
curl --fail http://127.0.0.1:8000/api/v1/health
systemctl restart fit5238
```

Before replacing the active release, create a SQLite backup while the app is
stopped. Keep older release directories until the new version has passed its
health, browser-flow and persistence checks.
