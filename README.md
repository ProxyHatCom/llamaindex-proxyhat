# llamaindex-proxyhat

Read the web in [LlamaIndex](https://www.llamaindex.ai) through [ProxyHat](https://proxyhat.com?utm_source=github&utm_medium=readme&utm_campaign=llamaindex) residential proxies — a web reader with rotating IPs, geo-targeting, and sticky sessions.

[![CI](https://github.com/ProxyHatCom/llamaindex-proxyhat/actions/workflows/ci.yml/badge.svg)](https://github.com/ProxyHatCom/llamaindex-proxyhat/actions/workflows/ci.yml)
[![Compatible with llama-index-core latest](https://github.com/ProxyHatCom/llamaindex-proxyhat/actions/workflows/compat.yml/badge.svg)](https://github.com/ProxyHatCom/llamaindex-proxyhat/actions/workflows/compat.yml)
[![PyPI](https://img.shields.io/pypi/v/llamaindex-proxyhat)](https://pypi.org/project/llamaindex-proxyhat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why

RAG pipelines that read the open web from datacenter IPs get blocked, rate-limited, and served bot-detection pages instead of content. This package routes LlamaIndex's web reads through ProxyHat's residential IPs (50M+ across 148+ countries) — a fresh IP per page by default, or one pinned IP for a whole multi-page load.

- **`ProxyHatWebReader`** — a `BaseReader` whose `load_data(urls)` fetches each URL and returns `Document` objects for indexing, retrieval, or summarization.

## Install

```bash
pip install llamaindex-proxyhat
```

`llama-index-core` is a peer — bring your own version (`>=0.10`), the same one your app and other LlamaIndex integrations already use.

## Quick start

Load pages as `Document` objects:

```python
from llamaindex_proxyhat import ProxyHatWebReader

# An API key auto-selects an active residential sub-user:
reader = ProxyHatWebReader(
    api_key="ph_your_api_key",
    country="us",
)

docs = reader.load_data(["https://example.com", "https://example.org"])

for doc in docs:
    print(doc.metadata["url"], doc.metadata["status_code"], len(doc.text))
```

Feed the documents straight into an index:

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(docs)
answer = index.as_query_engine().query("What does the page say?")
```

Get an API key at [proxyhat.com](https://proxyhat.com?utm_source=github&utm_medium=readme&utm_campaign=llamaindex).

## Credentials

Pass them explicitly or via environment variables — options win over env:

| Option | Env var | Notes |
|---|---|---|
| `api_key` | `PROXYHAT_API_KEY` | Auto-selects an active sub-user with remaining traffic |
| `sub_user` | `PROXYHAT_SUBUSER` | Pick a specific sub-user by uuid or name (with an API key) |
| `username` | `PROXYHAT_USERNAME` | Explicit gateway `proxy_username` (skips the API) |
| `password` | `PROXYHAT_PASSWORD` | Explicit gateway `proxy_password` |

## Targeting

```python
ProxyHatWebReader(
    api_key="ph_your_api_key",
    country="us",        # ISO code or "any" (default)
    region="california",
    city="new_york",
    filter="high",       # AI IP-quality tier
    sticky="30m",        # keep one IP across the whole load; omit for rotating
    protocol="http",     # or "socks5"
)
```

Each `Document` carries `text` (the response body) and `metadata` with `url`, `status_code`, and `content_type`.

### Rotating vs sticky

By default the reader is **rotating**: each page is fetched over a new connection with a stable gateway username, so ProxyHat hands out a fresh residential IP per page. Set `sticky` (e.g. `sticky="30m"` or `sticky=True`) to pin **one** residential IP across every page in the `load_data` call — the right choice for paginated sites, logged-in sessions, or anything that must look like a single user.

## How it works

`ProxyHatWebReader` subclasses [`BaseReader`](https://developers.llamaindex.ai) (`llama_index.core.readers.base`) and returns [`Document`](https://developers.llamaindex.ai) objects (`llama_index.core`). It resolves your gateway credentials once (via the official [`proxyhat`](https://pypi.org/project/proxyhat/) SDK — an API key auto-picks an active sub-user, or you supply `username`/`password` directly), then builds a ProxyHat gateway connection URL with the SDK's targeting grammar and fetches each URL through it with [`httpx`](https://www.python-httpx.org/). Rotating loads reuse a stable username so the gateway rotates the IP per connection; sticky loads reuse one session id (a single `httpx` client) so every request exits from the same IP.

Publishing to the [LlamaHub](https://llamahub.ai) / LlamaIndex integrations registry is a planned follow-up.

## License

MIT © [ProxyHat](https://proxyhat.com)
