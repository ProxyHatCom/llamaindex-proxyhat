"""Minimal LlamaIndex web reader over ProxyHat residential proxies.

    PROXYHAT_API_KEY=ph_xxx python examples/reader.py

Every page is fetched from a US residential IP. Pass ``sticky="30m"`` to pin one
IP across the whole load instead of rotating per page.
"""

import os

from llamaindex_proxyhat import ProxyHatWebReader

reader = ProxyHatWebReader(
    api_key=os.environ["PROXYHAT_API_KEY"],
    country="us",
)

docs = reader.load_data(["https://httpbin.org/ip", "https://example.com"])

for doc in docs:
    print(f"{doc.metadata['url']} -> {doc.metadata['status_code']} ({len(doc.text)} bytes)")
