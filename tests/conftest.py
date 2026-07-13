"""Shared test doubles — a fake ``httpx.Client`` that records how it was built."""

from __future__ import annotations

import pytest


class FakeResponse:
    def __init__(self, url, *, text="<html>ok</html>", status_code=200, content_type="text/html"):
        self.text = text
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self.url = url


class FakeClient:
    """Captures constructor kwargs (incl. ``proxy``) and requested URLs."""

    instances: list[FakeClient] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.requested: list[str] = []
        FakeClient.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, **kwargs):
        self.requested.append(url)
        return FakeResponse(url)

    @classmethod
    def reset(cls):
        cls.instances = []

    @classmethod
    def proxies(cls):
        return [inst.kwargs.get("proxy") for inst in cls.instances]


@pytest.fixture
def fake_client(monkeypatch):
    FakeClient.reset()
    monkeypatch.setattr("llamaindex_proxyhat.reader.httpx.Client", FakeClient)
    return FakeClient
