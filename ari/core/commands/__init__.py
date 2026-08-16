"""Generic, bot-wide cogs that aren't tied to any one feature.

    info_cog.py    Info cog — /support /invite
    utils_cog.py   Utils cog — /ping /uptime /help

Both are registered in `core/bot.py`'s `FEATURES` list. If a command here
ever grows real business logic (state, persistence, services), it's
outgrown this folder and belongs under `features/` instead — see
CLAUDE.md's "Adding a new feature".
"""
