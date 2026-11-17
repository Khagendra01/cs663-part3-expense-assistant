"""Pytest setup for the website tests.

On this VM the NO_PROXY list contains bracketed IPv6 entries like
[::1], which httpx cannot parse. Gradio builds an httpx client at
import time, so the import fails unless those entries are dropped
first. This drops only the bracketed entries and keeps localhost
and 127.0.0.1. On a normal machine it changes nothing.
"""

import os

for _key in ("NO_PROXY", "no_proxy"):
    _value = os.environ.get(_key)
    if _value:
        os.environ[_key] = ",".join(p for p in _value.split(",") if "[" not in p)
