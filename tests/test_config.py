"""Tests for ydiskarc.config.Config.

See openspec/changes/add-tls-verify-config.
"""

from ydiskarc.config import Config


class TestConfigDefaults:
    def test_default_verify_is_none(self):
        c = Config()
        assert c.verify is None

    def test_user_agent_default_is_generated(self):
        c = Config()
        assert c.user_agent is not None
        assert "ydiskarc" in c.user_agent


class TestConfigVerifyOverride:
    def test_explicit_true(self):
        c = Config(verify=True)
        assert c.verify is True

    def test_explicit_false(self):
        c = Config(verify=False)
        assert c.verify is False

    def test_explicit_path(self):
        c = Config(verify="/etc/pki/my-ca.pem")
        assert c.verify == "/etc/pki/my-ca.pem"


class TestConfigVerifyEnvOverride:
    def test_env_true(self, monkeypatch):
        monkeypatch.setenv("YDISKARC_TLS_VERIFY", "1")
        c = Config()
        assert c.verify is True

    def test_env_false(self, monkeypatch):
        monkeypatch.setenv("YDISKARC_TLS_VERIFY", "0")
        c = Config()
        assert c.verify is False

    def test_env_path(self, monkeypatch):
        monkeypatch.setenv("YDISKARC_TLS_VERIFY", "/tmp/ca.pem")
        c = Config()
        assert c.verify == "/tmp/ca.pem"

    def test_env_override_respects_explicit_constructor(self, monkeypatch):
        monkeypatch.setenv("YDISKARC_TLS_VERIFY", "/tmp/from-env.pem")
        c = Config(verify="/tmp/explicit.pem")
        assert c.verify == "/tmp/explicit.pem"

    def test_env_unset_keeps_default(self, monkeypatch):
        monkeypatch.delenv("YDISKARC_TLS_VERIFY", raising=False)
        c = Config()
        assert c.verify is None
