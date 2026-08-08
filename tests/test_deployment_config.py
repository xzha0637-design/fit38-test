from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_systemd_service_is_single_worker_and_loopback_only() -> None:
    service = (PROJECT_ROOT / "deploy" / "fit5238.service").read_text(
        encoding="utf-8"
    )

    for expected in [
        "User=fit5238",
        "--host 127.0.0.1",
        "--workers 1",
        "--no-access-log",
        "NoNewPrivileges=true",
        "ProtectSystem=strict",
        "ReadWritePaths=/var/lib/fit5238",
    ]:
        assert expected in service


def test_nginx_public_proxy_has_resource_and_feedback_controls() -> None:
    nginx = (PROJECT_ROOT / "deploy" / "nginx-site.conf").read_text(
        encoding="utf-8"
    )

    for expected in [
        "server 127.0.0.1:8000;",
        "access_log off;",
        "client_max_body_size 256k;",
        "zone=scoring_per_ip",
        "zone=batch_per_ip",
        "zone=workflow_per_ip",
        "location = /api/v1/feedback",
        "feedback_access_disabled",
        "Content-Security-Policy",
        'X-Content-Type-Options "nosniff"',
        'X-Frame-Options "DENY"',
    ]:
        assert expected in nginx

    assert "allow 45.196.221.124;" not in nginx
