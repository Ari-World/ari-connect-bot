"""Unit tests, mirroring `ari/`'s package layout — `tests/features/global_chat/`
tests `ari/features/global_chat/`, and so on. These `__init__.py` files
exist purely so pytest's default import mode doesn't collide on files that
share a basename (e.g. two different `test_presenters.py`); they're not
meaningful packages otherwise.

`pytest.ini` sets `pythonpath = ari`, so imports here match runtime
imports exactly: `from features.global_chat.state import GlobalChatState`,
not `from ari.features...`.
"""
