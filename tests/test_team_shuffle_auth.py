"""一時SQLiteで、Authorizationが除去される環境の認証を検証する。"""
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/valorant/team-shuffle"
HEADER = "X-Team-Shuffle-Authorization"


class TeamShuffleAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="shuffle-auth-")
        cls.addClassCleanup(cls.temp.cleanup)
        database = Path(cls.temp.name) / "auth.sqlite"
        uri = "sqlite:///" + database.as_posix()
        sys.path.insert(0, str(ROOT))
        with patch.dict(os.environ, {
            "FLASK_DEBUG": "1",
            "SECRET_KEY": "test-only",
            "MAIL_SERVER": "localhost",
            "MAIL_PORT": "1025",
            "MAIL_USE_TLS": "",
            "MAIL_USERNAME": "test",
            "MAIL_PASSWORD": "test",
            "MAIL_DEFAULT_SENDER": "test@example.invalid",
            "SQLALCHEMY_DATABASE_URI": uri,
            "OPENAI_API_KEY": "test-not-a-real-key",
            "TEAM_SHUFFLE_ALLOWED_ORIGINS": "http://localhost:4000,https://yamato080915.github.io",
        }):
            from app import app, db
        from models import ShuffleRoom, ShuffleParticipant
        cls.app, cls.db = app, db
        app.config.update(TESTING=True, MAIL_SUPPRESS_SEND=True)
        with app.app_context():
            if Path(db.engine.url.database).resolve() != database.resolve():
                raise RuntimeError("テスト用以外のDBへ接続しようとしました。")
            cls.engine = db.engine
            cls.addClassCleanup(cls.engine.dispose)
            db.metadata.create_all(bind=db.engine, tables=[
                ShuffleRoom.__table__, ShuffleParticipant.__table__,
            ])

    def setUp(self):
        self.client = self.app.test_client()
        self.room = str(uuid4())
        self.owner = secrets.token_hex(32)
        response = self.client.post(BASE + "/rooms", json={
            "id": self.room, "organizerToken": self.owner,
        })
        self.assertEqual(response.status_code, 200)

    def call(self, method, suffix, token=None, header=HEADER, **kwargs):
        headers = kwargs.pop("headers", {})
        if token is not None:
            headers[header] = "Bearer " + token
        return self.client.open(BASE + "/rooms/" + self.room + suffix,
                                method=method, headers=headers, **kwargs)

    def test_standard_header_still_works(self):
        response = self.call("GET", "/participants", self.owner, header="Authorization")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_missing_standard_header_uses_custom_header(self):
        self.assertEqual(self.call("GET", "/participants", self.owner).status_code, 200)

    def test_apache_redirected_header_is_supported(self):
        response = self.call("GET", "/participants", environ_overrides={
            "REDIRECT_HTTP_AUTHORIZATION": "Bearer " + self.owner,
        })
        self.assertEqual(response.status_code, 200)

    def test_matching_headers_are_accepted(self):
        response = self.call("GET", "/participants", self.owner, headers={
            "Authorization": "Bearer " + self.owner,
        })
        self.assertEqual(response.status_code, 200)

    def test_conflicting_or_malformed_headers_are_rejected(self):
        for value in ["", "Basic invalid", "Bearer invalid", "Bearer " + secrets.token_hex(32)]:
            with self.subTest(value=value[:12]):
                response = self.call("GET", "/participants", self.owner,
                                     headers={"Authorization": value})
                self.assertEqual(response.status_code, 401)
        response = self.call("GET", "/participants", self.owner, environ_overrides={
            "REDIRECT_HTTP_AUTHORIZATION": "Bearer " + secrets.token_hex(32),
        })
        self.assertEqual(response.status_code, 401)

    def test_missing_credentials_and_query_tokens_are_rejected(self):
        self.assertEqual(self.call("GET", "/participants").status_code, 401)
        response = self.call("GET", "/participants", query_string={"token": self.owner})
        self.assertEqual(response.status_code, 401)

    def test_custom_header_preserves_participant_identity_and_edit_lock(self):
        token = secrets.token_hex(32)
        body = dict(name="認証テスト", tier="gold", div=1, vc=True)
        response = self.call("PUT", "/registration", token, json=body)
        self.assertEqual(response.status_code, 200)
        participant = response.get_json()["participant"]
        # 旧ヘッダー経由の本人確認と同じIDになる。
        own = self.call("GET", "/registration", token, header="Authorization")
        self.assertEqual(own.get_json()["participant"]["id"], participant["id"])
        self.assertEqual(self.call("GET", "/participants", token).status_code, 403)
        snapshot = self.call("GET", "/participants", self.owner).get_json()
        locked = self.call("PUT", "/edit-locks", self.owner, json={
            "operationId": str(uuid4()),
            "expectedRevision": snapshot["room"]["revision"],
            "participantIds": [participant["id"]],
        })
        self.assertEqual(locked.status_code, 200)
        rejected = self.call("PUT", "/registration", token, json=dict(body, name="変更"))
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(rejected.get_json()["code"], "locked")
        self.assertEqual(self.call("POST", "/close", self.owner).status_code, 200)

    def test_custom_header_does_not_grant_another_room_access(self):
        self.assertEqual(self.call("GET", "/participants", secrets.token_hex(32)).status_code, 403)
        self.assertEqual(self.call("GET", "/participants", "invalid").status_code, 401)

    def test_cors_allows_both_headers_only_from_allowed_origins(self):
        for origin in ["http://localhost:4000", "https://yamato080915.github.io"]:
            response = self.call("OPTIONS", "/registration", headers={
                "Origin": origin,
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "authorization,content-type,x-team-shuffle-authorization",
            })
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
            allowed = response.headers.get("Access-Control-Allow-Headers", "").lower()
            self.assertIn("authorization", allowed)
            self.assertIn("x-team-shuffle-authorization", allowed)
            self.assertEqual(response.headers.get("Access-Control-Max-Age"), "600")
            self.assertNotIn("Access-Control-Allow-Credentials", response.headers)
        denied = self.call("OPTIONS", "/registration", headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": HEADER,
        })
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)


if __name__ == "__main__":
    unittest.main()
