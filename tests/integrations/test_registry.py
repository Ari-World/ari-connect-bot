from integrations import registry, fenderbot
from integrations.registry import TrustedBotIntegration


class TestIsTrustedBot:
    def test_true_for_a_registered_bot(self, monkeypatch):
        monkeypatch.setattr(registry, "_trusted_bots", [TrustedBotIntegration(name="FenderBot", user_id=111)])
        assert registry.is_trusted_bot(111) is True

    def test_false_for_an_unregistered_bot(self, monkeypatch):
        monkeypatch.setattr(registry, "_trusted_bots", [TrustedBotIntegration(name="FenderBot", user_id=111)])
        assert registry.is_trusted_bot(999) is False

    def test_false_when_nothing_is_registered(self, monkeypatch):
        monkeypatch.setattr(registry, "_trusted_bots", [])
        assert registry.is_trusted_bot(111) is False


class TestLoadIntegrations:
    def test_skips_integrations_with_no_env_var_set(self, monkeypatch):
        monkeypatch.delenv("FENDERBOT_USER_ID", raising=False)
        result = registry.load_integrations()
        assert result == []
        assert registry.is_trusted_bot(123) is False

    def test_includes_configured_integrations(self, monkeypatch):
        monkeypatch.setenv("FENDERBOT_USER_ID", "555")
        result = registry.load_integrations()
        assert result == [TrustedBotIntegration(name="FenderBot", user_id=555)]
        assert registry.is_trusted_bot(555) is True


class TestFenderbotBuild:
    def test_returns_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("FENDERBOT_USER_ID", raising=False)
        assert fenderbot.build() is None

    def test_returns_integration_when_set(self, monkeypatch):
        monkeypatch.setenv("FENDERBOT_USER_ID", "42")
        result = fenderbot.build()
        assert result == TrustedBotIntegration(name="FenderBot", user_id=42)
