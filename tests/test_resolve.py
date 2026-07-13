from types import SimpleNamespace

import pytest

from llamaindex_proxyhat._resolve import resolve_credentials


def _user(uuid, proxy_username, *, name=None, traffic_limit=0, used_traffic=0, suspended_at=None):
    return SimpleNamespace(
        uuid=uuid,
        name=name,
        proxy_username=proxy_username,
        proxy_password="pw",
        traffic_limit=traffic_limit,
        used_traffic=used_traffic,
        suspended_at=suspended_at,
    )


def _patch_sdk(monkeypatch, users):
    fake_client = SimpleNamespace(sub_users=SimpleNamespace(list=lambda: users))
    monkeypatch.setattr("llamaindex_proxyhat._resolve.ProxyHat", lambda **kw: fake_client)


class TestExplicitCredentials:
    def test_username_password_wins(self, monkeypatch):
        monkeypatch.delenv("PROXYHAT_API_KEY", raising=False)
        assert resolve_credentials(username="u", password="p") == ("u", "p")

    def test_reads_env(self, monkeypatch):
        monkeypatch.setenv("PROXYHAT_USERNAME", "envu")
        monkeypatch.setenv("PROXYHAT_PASSWORD", "envp")
        assert resolve_credentials() == ("envu", "envp")

    def test_options_win_over_env(self, monkeypatch):
        monkeypatch.setenv("PROXYHAT_USERNAME", "envu")
        monkeypatch.setenv("PROXYHAT_PASSWORD", "envp")
        assert resolve_credentials(username="optu", password="optp") == ("optu", "optp")

    def test_raises_without_anything(self, monkeypatch):
        for var in ("PROXYHAT_API_KEY", "PROXYHAT_USERNAME", "PROXYHAT_PASSWORD"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(ValueError):
            resolve_credentials()


class TestApiKeyResolution:
    def test_picks_first_active_sub_user(self, monkeypatch):
        _patch_sdk(
            monkeypatch,
            [
                _user("s", "susp", traffic_limit=100, used_traffic=1, suspended_at="2026-01-01"),
                _user("g", "good", traffic_limit=0, used_traffic=9),
            ],
        )
        assert resolve_credentials(api_key="ph_key") == ("good", "pw")

    def test_skips_out_of_traffic(self, monkeypatch):
        _patch_sdk(
            monkeypatch,
            [
                _user("x", "x", traffic_limit=100, used_traffic=100),
                _user("y", "yy", traffic_limit=100, used_traffic=1),
            ],
        )
        assert resolve_credentials(api_key="ph_key") == ("yy", "pw")

    def test_selects_named_sub_user(self, monkeypatch):
        _patch_sdk(
            monkeypatch,
            [
                _user("a", "aaa", name="alpha"),
                _user("b", "bbb", name="beta"),
            ],
        )
        assert resolve_credentials(api_key="ph_key", sub_user="beta") == ("bbb", "pw")

    def test_raises_when_none_usable(self, monkeypatch):
        _patch_sdk(monkeypatch, [_user("x", "x", traffic_limit=100, used_traffic=100)])
        with pytest.raises(ValueError):
            resolve_credentials(api_key="ph_key")
