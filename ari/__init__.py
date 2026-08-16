"""Ari Connect — a Discord bot that relays chat across servers via
lobby-based, webhook-backed channel connections.

Run it with `cd ari && python __main__.py` (not `python -m ari` from the
repo root — see CLAUDE.md for why). Top-level package layout:

    core/           bot chassis — startup, config, logging, generic commands
    features/       self-contained product features (global_chat, ...)
    integrations/   external bot-to-bot integrations (e.g. FenderBot)

See /CLAUDE.md at the repo root for the full architecture guide.
"""
