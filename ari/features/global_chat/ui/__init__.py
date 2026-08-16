"""global_chat's Discord-facing presentation layer.

    views.py         interactive components — CreateLobbyModal, LobbyPagination,
                      DropDown, DynamicDropDown, DynamicChoice
    presenters.py     pure functions returning discord.Embed — no ctx.send in
                      here. Grouped here as the "how this looks" layer, even
                      though `cogs/` imports it too (`from ..ui import
                      presenters`) — it's not exclusively for views.py's use.

`views.py`'s components call into `services/` for anything that reads/
writes data (e.g. `CreateLobbyModal.on_submit` calls
`LobbyService.create_lobby` + `GuildConnectionService.connect`) rather
than touching the repository or cache directly — the same "no business
logic in the presentation layer" rule as `cogs/`.
"""
