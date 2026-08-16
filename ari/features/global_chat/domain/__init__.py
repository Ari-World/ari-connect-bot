"""The domain layer — `models.py` holds one `@dataclass` per shape
global_chat persists: `Lobby`, `LobbyConfig` (nesting `LobbyDetails`,
`ModerationConfig`, `LogConfig`), `Connection`, `MutedUser`,
`BannedContent`, `ModeratorRole` (nesting `ModeratorAssignment`) — plus
`LobbyView`, a read-only join of `Lobby` + `LobbyConfig` that most
commands actually want.

Each has `to_document()`/`from_document()` for the dict <-> dataclass
boundary; `persistence/repository.py` is the only file that calls them —
everything else (state, services, cogs) works with the dataclasses
directly. They're mutable on purpose, not frozen: `persistence/state.py`
and the services append/remove/mutate them in place.
"""
