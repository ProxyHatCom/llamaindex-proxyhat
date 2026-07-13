from llama_index.core import Document

from llamaindex_proxyhat import ProxyHatWebReader


def make_reader(**kwargs):
    kwargs.setdefault("username", "ph-1")
    kwargs.setdefault("password", "pw")
    return ProxyHatWebReader(**kwargs)


class TestProxyUrl:
    def test_geo_reflected_in_proxy(self, fake_client):
        reader = make_reader(country="us")
        docs = reader.load_data("https://example.com")
        assert len(docs) == 1
        proxy = fake_client.proxies()[0]
        assert proxy == "http://ph-1-country-us:pw@gate.proxyhat.com:8080"

    def test_rotating_builds_fresh_client_per_url_without_sid(self, fake_client):
        reader = make_reader(country="de")
        reader.load_data(["https://a.com", "https://b.com"])
        proxies = fake_client.proxies()
        assert len(proxies) == 2  # a fresh connection per page
        assert all("ph-1-country-de" in p for p in proxies)
        assert all("-sid-" not in p for p in proxies)

    def test_sticky_pins_one_ip_across_pages(self, fake_client):
        reader = make_reader(sticky="30m")
        reader.load_data(["https://a.com", "https://b.com"])
        proxies = fake_client.proxies()
        assert len(proxies) == 1  # a single shared client
        assert "-sid-" in proxies[0]
        assert "-ttl-30m" in proxies[0]

    def test_region_and_city_reflected(self, fake_client):
        reader = make_reader(country="us", region="california", city="new york")
        reader.load_data("https://example.com")
        proxy = fake_client.proxies()[0]
        assert "-region-california" in proxy
        assert "-city-new_york" in proxy

    def test_socks5_protocol(self, fake_client):
        reader = make_reader(protocol="socks5")
        reader.load_data("https://example.com")
        assert fake_client.proxies()[0].startswith("socks5://")
        assert ":1080" in fake_client.proxies()[0]


class TestDocuments:
    def test_document_content_and_metadata(self, fake_client):
        reader = make_reader()
        docs = reader.load_data("https://example.com/page")
        doc = docs[0]
        assert isinstance(doc, Document)
        assert doc.text == "<html>ok</html>"
        assert doc.metadata["url"] == "https://example.com/page"
        assert doc.metadata["status_code"] == 200
        assert doc.metadata["content_type"] == "text/html"

    def test_load_data_returns_document_per_url(self, fake_client):
        reader = make_reader()
        docs = reader.load_data(["https://a.com", "https://b.com"])
        assert [d.metadata["url"] for d in docs] == ["https://a.com", "https://b.com"]


class TestApiKeyResolution:
    def test_reader_resolves_sub_user(self, fake_client, monkeypatch):
        from types import SimpleNamespace

        users = [
            SimpleNamespace(
                uuid="g",
                name=None,
                proxy_username="good",
                proxy_password="pw",
                traffic_limit=0,
                used_traffic=1,
                suspended_at=None,
            )
        ]
        monkeypatch.setattr(
            "llamaindex_proxyhat._resolve.ProxyHat",
            lambda **kw: SimpleNamespace(sub_users=SimpleNamespace(list=lambda: users)),
        )
        reader = ProxyHatWebReader(api_key="ph_key", country="us")
        reader.load_data("https://example.com")
        assert "good-country-us" in fake_client.proxies()[0]
