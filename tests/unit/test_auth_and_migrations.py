"""Unit tests for scrypt password security, HS256 JWT tokens, email domain policy, and Postgres migration parity."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi import HTTPException

from backend.api import config as config_mod
from backend.authentication.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    validate_college_domain,
    verify_password,
)
from backend.migrations.sqlite_to_postgres import (
    REQUIRED_TABLES,
    extract_postgres_ddl_tables,
    migrate_sqlite_to_postgres,
)


def test_scrypt_password_hashing_salted_and_verifiable() -> None:
    h1 = hash_password("bmsit_pass_2026")
    h2 = hash_password("bmsit_pass_2026")
    assert h1.startswith("scrypt$16384$8$1$")
    assert h1 != h2  # unique random salt per digest
    assert verify_password("bmsit_pass_2026", h1) is True
    assert verify_password("wrong_pass", h1) is False
    assert verify_password("anything", "corrupt_hash_format") is False


def test_jwt_issue_decode_tamper_and_expiration() -> None:
    token, expires_in = create_access_token("usr_001", "student@bmsit.in", "student")
    assert expires_in >= 60
    claims = decode_access_token(token)
    assert claims["sub"] == "usr_001"
    assert claims["role"] == "student"

    # Tampering signature raises HTTP 401
    tampered = token[:-4] + "abcd"
    with pytest.raises(HTTPException) as exc_tamper:
        decode_access_token(tampered)
    assert exc_tamper.value.status_code == 401

    # Expired token raises HTTP 401
    settings = config_mod.get_settings()
    expired = jwt.encode(
        {
            "sub": "usr_001",
            "exp": int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp()),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_exp:
        decode_access_token(expired)
    assert exc_exp.value.status_code == 401


def test_college_domain_enforcement_toggle(monkeypatch) -> None:
    monkeypatch.setenv("RESTRICT_COLLEGE_EMAIL_DOMAIN", "true")
    monkeypatch.setenv("ALLOWED_AUTH_DOMAINS", "bmsit.in,bmsit.ac.in")
    config_mod.get_settings.cache_clear()
    try:
        assert validate_college_domain("Student.Name@BMSIT.IN") == "student.name@bmsit.in"
        with pytest.raises(HTTPException) as exc_bad:
            validate_college_domain("outsider@gmail.com")
        assert exc_bad.value.status_code == 403
    finally:
        config_mod.get_settings.cache_clear()


def test_postgres_ddl_and_sqlite_dry_run_migration_parity(tmp_path: Path) -> None:
    ddl_path = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "001_postgres_initial.sql"
    assert ddl_path.is_file()
    ddl_tables = extract_postgres_ddl_tables(ddl_path)
    for table in REQUIRED_TABLES:
        assert table in ddl_tables

    sqlite_file = tmp_path / "migration_test.db"
    report = migrate_sqlite_to_postgres(sqlite_file, ddl_path=ddl_path, dry_run=True)
    assert report["ddl_tables_verified"] is True
    assert report["missing_ddl_tables"] == []
    assert report["mode"] == "dry_run"
    assert set(report["sqlite_table_counts"].keys()) == set(REQUIRED_TABLES)

