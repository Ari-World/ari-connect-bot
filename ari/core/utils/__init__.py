"""Shared helper *modules* — plain functions, not Discord cogs.

    chat_formatting.py   humanize_timedelta / humanize_list
    utility.py           generate_uuid, the Color enum

Not to be confused with `core/commands/` (the `Utils` *cog*, i.e.
`/ping` `/uptime` `/help`) — this folder holds formatting/utility code
that anything in the bot might import, not a set of Discord commands.
"""
