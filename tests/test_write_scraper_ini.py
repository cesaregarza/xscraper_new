from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path


def test_write_scraper_ini_uses_shared_config_template(tmp_path: Path) -> None:
    script = Path(__file__).parent.parent / "scripts" / "write_scraper_ini.sh"
    shared_config = (
        "ftoken_url = https://example.com/api/znca/f\n\n"
        "[options]\n"
        "user_agent = xscraper-test/1.0\n\n"
        "[nxapi]\n"
        "nxapi_client_id = client-id\n"
        "nxapi_client_assertion_kid = test-kid\n"
    )
    env = os.environ | {
        "SCRAPER_SHARED_CONFIG_B64": base64.b64encode(
            shared_config.encode("utf-8")
        ).decode("ascii"),
    }

    subprocess.run(
        [script, "session-one|session-two"],
        cwd=tmp_path,
        env=env,
        check=True,
        text=True,
    )

    first = (tmp_path / "SCRAPER_0.ini").read_text(encoding="utf-8")
    second = (tmp_path / "SCRAPER_1.ini").read_text(encoding="utf-8")

    assert "session_token = session-one" in first
    assert "session_token = session-two" in second
    assert "ftoken_url = https://example.com/api/znca/f" in first
    assert "gtoken =" not in first
    assert "bullet_token =" not in first
    assert "nxapi_client_id = client-id" in first


def test_write_scraper_ini_uses_env_fallback(tmp_path: Path) -> None:
    script = Path(__file__).parent.parent / "scripts" / "write_scraper_ini.sh"
    env = os.environ | {
        "SCRAPER_FTOKEN_URL": "https://example.com/api/znca/f",
        "SCRAPER_USER_AGENT": "xscraper-test/1.0",
        "SCRAPER_NXAPI_CLIENT_ID": "client-id",
        "SCRAPER_NXAPI_SCOPE": "ca:gf",
        "SCRAPER_NXAPI_CLIENT_VERSION": "test-version",
        "SCRAPER_NXAPI_CLIENT_ASSERTION_PRIVATE_KEY_PATH": (
            "/tmp/test-private.pem"
        ),
        "SCRAPER_NXAPI_CLIENT_ASSERTION_JKU": (
            "https://example.com/.well-known/jwks.json"
        ),
        "SCRAPER_NXAPI_CLIENT_ASSERTION_KID": "test-kid",
    }

    subprocess.run(
        [script, "session-one"],
        cwd=tmp_path,
        env=env,
        check=True,
        text=True,
    )

    rendered = (tmp_path / "SCRAPER_0.ini").read_text(encoding="utf-8")

    assert "session_token = session-one" in rendered
    assert "ftoken_url = https://example.com/api/znca/f" in rendered
    assert "user_agent = xscraper-test/1.0" in rendered
    assert "nxapi_client_id = client-id" in rendered
    assert "nxapi_scope = ca:gf" in rendered
    assert "nxapi_client_version = test-version" in rendered
    assert "nxapi_client_assertion_kid = test-kid" in rendered
    assert "gtoken =" not in rendered
    assert "bullet_token =" not in rendered
