"""Lobby lookup, validation, and creation.

No Discord API calls in here (that's `GuildConnectionService`'s job) —
persistence goes through the repository layer, same pattern
`GuildConnectionService` uses. `lobby_data` (owner/guild/lobby_id) and
`lobby_config` (title/description/topics/limit) are two separate
collections; `find_lobby_details` is the one place that joins them, so
nothing else in the feature needs to know they're split.
"""
from typing import List, Optional

from ..domain.models import Connection, Lobby, LobbyConfig, LobbyDetails, LobbyView
from ..persistence.state import GlobalChatState


class LobbyService:
    def __init__(self, state: GlobalChatState, repository=None):
        self.state = state
        self.repos = repository

    def find_connection(self, guild_id: int, channel_id: int) -> Optional[Connection]:
        for connection in self.state.connection:
            if connection.guild_id == guild_id and connection.channel_id == channel_id:
                return connection
        return None

    def find_lobby_details(self, lobby_id: str) -> Optional[LobbyView]:
        """The lobby's display info, joined from `lobby_data` + `lobby_config`.

        Returns None if the lobby_id doesn't exist in both collections —
        callers should treat that as "lobby not found", not crash on a
        missing attribute (the bug this replaces: several call sites used
        to read title/description/topics/limit straight off a `Lobby`,
        which never has those fields).
        """
        lobby = next((entry for entry in self.state.lobby_data if entry.lobby_id == lobby_id), None)
        config_entry = next((entry for entry in self.state.lobby_config if entry.lobby_id == lobby_id), None)
        if not lobby or not config_entry:
            return None

        details = config_entry.lobby_config
        return LobbyView(
            lobby_id=lobby.lobby_id,
            guild_id=lobby.guild_id,
            title=details.title,
            description=details.description,
            topics=details.topics,
            limit=details.limit,
            footer_message=details.footer,
        )

    def connections_for_lobby(self, lobby_id: str) -> List[Connection]:
        return [connection for connection in self.state.connection if connection.lobby_id == lobby_id]

    def has_room(self, lobby_view: LobbyView) -> bool:
        return self.state.get_lobby_length(lobby_view.lobby_id) < lobby_view.limit

    def list_lobby_summaries(self) -> List[LobbyView]:
        """Every lobby with its display info + live connection count — the
        data `/lobbies` pagination browses. Reuses `find_lobby_details`
        rather than re-joining `lobby_data`/`lobby_config` a second way."""
        summaries = []
        for lobby in self.state.lobby_data:
            details = self.find_lobby_details(lobby.lobby_id)
            if details:
                details.connection_count = self.state.get_lobby_length(details.lobby_id)
                summaries.append(details)
        return summaries

    async def create_lobby(
            self,
            lobby_id: str,
            guild_id: int,
            guild_name: str,
            owner_id: int,
            title: str,
            description: str,
            topics: List[str]) -> Lobby:
        """Creates the `lobby_data` + `lobby_config` records for a new lobby
        (not the connection/webhook — that's
        `GuildConnectionService.connect()`, called separately)."""
        lobby = Lobby(lobby_id=lobby_id, guild_id=guild_id, guild_name=guild_name, owner_id=owner_id)
        lobby = await self.repos.lobby_repository.create(lobby)
        self.state.lobby_data.append(lobby)

        config = LobbyConfig(
            lobby_id=lobby_id,
            lobby_config=LobbyDetails(title=title, description=description, topics=topics),
        )
        config = await self.repos.lobby_config_repository.create(config)
        self.state.lobby_config.append(config)

        return lobby
