"""Credential resolution for llamaindex-proxyhat.

Mirrors the other ProxyHat integrations: explicit options win over environment
variables. Either an API key (which auto-selects an active residential sub-user
via the official ``proxyhat`` SDK) or an explicit gateway ``username`` +
``password`` pair. Everything except the sub-user lookup is offline.
"""

from __future__ import annotations

import os

from proxyhat import ProxyHat

# Targeting knobs shared across ProxyHat integrations.
TARGETING_KEYS = ("country", "region", "city", "sticky", "filter")


def resolve_credentials(
    *,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
    sub_user: str | None = None,
) -> tuple[str, str]:
    """Resolve a gateway ``(proxy_username, proxy_password)`` pair.

    Options win over environment variables (``PROXYHAT_API_KEY``,
    ``PROXYHAT_USERNAME``, ``PROXYHAT_PASSWORD``, ``PROXYHAT_SUBUSER``). Explicit
    ``username`` + ``password`` skip the API entirely; otherwise an ``api_key``
    auto-selects an active sub-user with remaining traffic.
    """
    api_key = api_key or os.environ.get("PROXYHAT_API_KEY")
    username = username or os.environ.get("PROXYHAT_USERNAME")
    password = password or os.environ.get("PROXYHAT_PASSWORD")
    sub_user = sub_user or os.environ.get("PROXYHAT_SUBUSER")

    if username and password:
        return username, password
    if api_key:
        return _resolve_sub_user(api_key, sub_user)
    raise ValueError("llamaindex-proxyhat: set PROXYHAT_API_KEY, or PROXYHAT_USERNAME + PROXYHAT_PASSWORD.")


def _resolve_sub_user(api_key: str, want: str | None) -> tuple[str, str]:
    users = ProxyHat(api_key=api_key).sub_users.list()
    usable = [u for u in users if not u.suspended_at and (u.traffic_limit == 0 or u.used_traffic < u.traffic_limit)]
    if want:
        chosen = next((u for u in users if u.uuid == want or u.name == want), None)
    else:
        chosen = usable[0] if usable else None
    if chosen is None or not chosen.proxy_username or not chosen.proxy_password:
        raise ValueError("llamaindex-proxyhat: no usable ProxyHat sub-user found (suspended or out of traffic).")
    return chosen.proxy_username, chosen.proxy_password
