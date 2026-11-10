"""Integration tests for JWT auth, RBAC enforcement, per-user storage quotas, admin telemetry, and cache cleanup."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import create_synthetic_image


def test_campus_auth_rbac_quota_enforcement_and_cleanup_api(isolated_env) -> None:
    client, settings, tmp_path = isolated_env

    # 1. Protected endpoints strictly require valid Bearer JWT
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/admin/overview").status_code == 401

    # 2. Register a new BMSIT student account (cannot self-escalate to 'admin')
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Ananya Sharma",
            "email": "ananya.cs@bmsit.in",
            "password": "securepassword123",
            "department": "Computer Science & Engineering",
            "role": "admin",
        },
    )
    assert reg_res.status_code == 201
    student_auth = reg_res.json()
    student_token = student_auth["access_token"]
    student_id = student_auth["user"]["id"]
    assert student_auth["user"]["role"] == "student"
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Duplicate email registration rejected cleanly with HTTP 409
    dup_res = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Duplicate",
            "email": "ananya.cs@bmsit.in",
            "password": "anotherpassword",
        },
    )
    assert dup_res.status_code == 409

    # 4. Authenticated student /me works, while /admin/* strictly rejects student role with 403
    me_res = client.get("/api/v1/auth/me", headers=student_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "ananya.cs@bmsit.in"
    assert client.get("/api/v1/admin/overview", headers=student_headers).status_code == 403
    assert client.post("/api/v1/admin/cleanup", json={}, headers=student_headers).status_code == 403

    # 5. Seeded Club Admin login succeeds and opens live diagnostics & user quota control
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "media.club@bmsit.in", "password": "bmsit2026admin"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    ov_res = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert ov_res.status_code == 200
    ov = ov_res.json()
    assert ov["system"]["cpu_cores"] >= 1
    assert ov["system"]["memory_total_gb"] > 0
    assert ov["database_engine"] == "sqlite"

    mig_res = client.get("/api/v1/admin/migration-status", headers=admin_headers)
    assert mig_res.status_code == 200
    assert mig_res.json()["postgres_ddl_ready"] is True
    assert mig_res.json()["table_counts"]["users"] >= 2

    # 6. Enforce per-student storage quota cap -> lower student quota to 1500 bytes, try uploading ~larger PNG
    sample_png = create_synthetic_image(tmp_path / "quota_sample.png", width=800, height=600)
    png_bytes = sample_png.read_bytes()
    assert len(png_bytes) > 1500

    shrink_res = client.patch(
        f"/api/v1/admin/users/{student_id}",
        json={"storage_quota_bytes": 1500},
        headers=admin_headers,
    )
    assert shrink_res.status_code == 200
    assert shrink_res.json()["storage_quota_bytes"] == 1500

    blocked_up = client.post(
        "/api/v1/media/upload",
        files=[("files", ("too_big.png", png_bytes, "image/png"))],
        headers=student_headers,
    )
    assert blocked_up.status_code == 413
    assert "quota exceeded" in blocked_up.json()["detail"].lower()

    # Expand quota -> upload succeeds and reflects accurate owner_id & used_bytes
    expand_res = client.patch(
        f"/api/v1/admin/users/{student_id}",
        json={"storage_quota_gb": 1.0},
        headers=admin_headers,
    )
    assert expand_res.status_code == 200

    ok_up = client.post(
        "/api/v1/media/upload",
        files=[("files", ("allowed.png", png_bytes, "image/png"))],
        headers=student_headers,
    )
    assert ok_up.status_code == 200
    uploaded_asset = ok_up.json()["uploaded"][0]
    assert uploaded_asset["owner_id"] == student_id
    uploaded_src = Path(uploaded_asset["file_path"])
    assert uploaded_src.is_file()

    quota_res = client.get("/api/v1/auth/quota", headers=student_headers)
    assert quota_res.status_code == 200
    assert quota_res.json()["used_bytes"] == len(png_bytes)

    # 7. Cross-student deletion guard: another student cannot delete Ananya's asset
    other_reg = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Other Student",
            "email": "other.student@bmsit.in",
            "password": "password1234",
        },
    )
    other_headers = {"Authorization": f"Bearer {other_reg.json()['access_token']}"}
    assert client.delete(f"/api/v1/media/{uploaded_asset['id']}", headers=other_headers).status_code == 403

    # 8. Automated disk cache cleanup purges temp cache & old renders without deleting uploaded source assets
    stale_seg = settings.CACHE_DIR / "segments" / "stale_demo.mp4"
    stale_seg.parent.mkdir(parents=True, exist_ok=True)
    stale_seg.write_bytes(b"0" * 4096)
    stale_render = settings.RENDER_DIR / "old_export.mp4"
    stale_render.write_bytes(b"1" * 8192)

    clean_res = client.post(
        "/api/v1/admin/cleanup",
        json={"purge_cache": True, "purge_expired_renders": True, "max_age_hours": 0},
        headers=admin_headers,
    )
    assert clean_res.status_code == 200
    clean_body = clean_res.json()
    assert clean_body["files_removed"] >= 2
    assert clean_body["freed_bytes"] >= 12288
    assert not stale_seg.exists()
    assert not stale_render.exists()
    assert uploaded_src.is_file()  # User source asset untouched

