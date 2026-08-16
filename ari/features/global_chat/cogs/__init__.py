"""global_chat's Discord-facing cogs — thin by design. Each command method
parses input, calls a `services/` method, renders the result via
`presenters.py` if there's an embed involved, and sends. No business logic
should live here.

    commands.py             Chat cog — /connect /unlink /switch /current /createlobby /lobbies /lobby_show /report
    moderation_commands.py  Moderation cog — /mute /unmute /delete /add_badword etc.
    settings_commands.py    Config cog — /settings (UI only, no persistence — see /CLAUDE.md)
    listeners.py             EventListeners cog — on_message/on_message_edit/on_message_delete
"""
