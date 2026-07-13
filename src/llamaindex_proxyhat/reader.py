"""``ProxyHatWebReader`` — a LlamaIndex web reader over ProxyHat residential proxies."""

from __future__ import annotations

from collections.abc import Iterable

import httpx
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader
from proxyhat import build_connection_url

from llamaindex_proxyhat._resolve import resolve_credentials


class ProxyHatWebReader(BaseReader):
    """Load one or more URLs through ProxyHat residential proxies as ``Document`` objects.

    Each URL is fetched with ``httpx`` through the ProxyHat gateway; the response
    body becomes ``Document.text`` and request/response facts land in
    ``Document.metadata`` (``url``, ``status_code``, ``content_type``).

    Rotating by default — a fresh residential IP per page. Set ``sticky`` to keep
    a single IP pinned across the whole load (useful for paginated sites or
    session-scoped crawls).

    ```python
    from llamaindex_proxyhat import ProxyHatWebReader

    reader = ProxyHatWebReader(
        api_key="ph_your_api_key",   # or username=/password=
        country="us",
    )
    docs = reader.load_data(["https://example.com", "https://example.org"])
    ```
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
        sub_user: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        sticky: bool | str | None = None,
        filter: str | None = None,
        protocol: str = "http",
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,
    ) -> None:
        super().__init__()
        self._username, self._password = resolve_credentials(
            api_key=api_key, username=username, password=password, sub_user=sub_user
        )
        self.targeting: dict[str, bool | str | None] = {
            "country": country,
            "region": region,
            "city": city,
            "sticky": sticky,
            "filter": filter,
        }
        self.protocol = protocol
        self.timeout = timeout
        self.headers = headers
        self.follow_redirects = follow_redirects

    @property
    def _is_sticky(self) -> bool:
        sticky = self.targeting.get("sticky")
        return sticky is not None and sticky is not False

    def _build_proxy_url(self) -> str:
        kwargs = {key: value for key, value in self.targeting.items() if value is not None}
        return build_connection_url(
            username=self._username,
            password=self._password,
            protocol=self.protocol,
            **kwargs,
        )

    def _client(self, proxy_url: str) -> httpx.Client:
        return httpx.Client(
            proxy=proxy_url,
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=self.follow_redirects,
        )

    @staticmethod
    def _to_document(source: str, response: httpx.Response) -> Document:
        return Document(
            text=response.text,
            metadata={
                "url": source,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
            },
        )

    def load_data(self, urls: str | Iterable[str]) -> list[Document]:
        """Fetch each URL through ProxyHat and return a list of ``Document`` objects.

        Rotating (default): a fresh connection per page over a stable gateway
        username, so the gateway hands out a new residential IP each time. Sticky:
        one pinned session reused across every page in the load — one IP throughout.
        """
        targets = [urls] if isinstance(urls, str) else list(urls)
        docs: list[Document] = []
        if self._is_sticky:
            # One gateway username (one sid) reused across every page → one pinned IP.
            proxy_url = self._build_proxy_url()
            with self._client(proxy_url) as client:
                for url in targets:
                    docs.append(self._to_document(url, client.get(url)))
        else:
            # A fresh connection per page over a stable username → a fresh residential IP each time.
            for url in targets:
                with self._client(self._build_proxy_url()) as client:
                    docs.append(self._to_document(url, client.get(url)))
        return docs
