import asyncio

from features.global_chat.domain.models import Connection, Lobby, LobbyConfig, LobbyDetails, LobbyView
from features.global_chat.services.lobby_service import LobbyService
from features.global_chat.persistence.state import GlobalChatState


def make_state(lobby_data=None, lobby_config=None, connection=None):
    state = GlobalChatState.__new__(GlobalChatState)
    state.lobby_data = lobby_data or []
    state.lobby_config = lobby_config or []
    state.connection = connection or []
    return state


class FakeSubRepository:
    """Mirrors the real repository's create() contract: takes an entity,
    sets its _id, returns the same entity — not a raw insert result."""
    def __init__(self):
        self.created = []

    async def create(self, entity):
        entity._id = "fake-id"
        self.created.append(entity)
        return entity


class FakeRepository:
    def __init__(self):
        self.lobby_repository = FakeSubRepository()
        self.lobby_config_repository = FakeSubRepository()


class TestFindConnection:
    def test_finds_a_matching_connection(self):
        connection = Connection(guild_id=1, channel_id=10, lobby_id="abc", webhook="w", guild_name="A")
        service = LobbyService(make_state(connection=[connection]))
        assert service.find_connection(1, 10) == connection

    def test_returns_none_when_not_connected(self):
        service = LobbyService(make_state(connection=[]))
        assert service.find_connection(1, 10) is None

    def test_does_not_match_the_wrong_channel(self):
        service = LobbyService(make_state(connection=[
            Connection(guild_id=1, channel_id=10, lobby_id="abc", webhook="w", guild_name="A"),
        ]))
        assert service.find_connection(1, 999) is None


class TestFindLobbyDetails:
    def test_joins_lobby_data_and_lobby_config(self):
        service = LobbyService(make_state(
            lobby_data=[Lobby(lobby_id="abc", guild_id=1, guild_name="A", owner_id=5)],
            lobby_config=[LobbyConfig(
                lobby_id="abc",
                lobby_config=LobbyDetails(title="My Lobby", description="desc", topics=["a"], limit=20, footer="f"),
            )],
        ))
        details = service.find_lobby_details("abc")
        assert details == LobbyView(
            lobby_id="abc", guild_id=1, title="My Lobby", description="desc",
            topics=["a"], limit=20, footer_message="f",
        )

    def test_returns_none_when_lobby_data_is_missing(self):
        service = LobbyService(make_state(
            lobby_data=[],
            lobby_config=[LobbyConfig(lobby_id="abc", lobby_config=LobbyDetails(title="x", description="d", topics=[], limit=1))],
        ))
        assert service.find_lobby_details("abc") is None

    def test_returns_none_when_lobby_config_is_missing(self):
        # This is the bug being fixed: Lobby entries alone don't carry
        # title/description/topics/limit — those only exist in LobbyConfig.
        service = LobbyService(make_state(
            lobby_data=[Lobby(lobby_id="abc", guild_id=1, guild_name="A", owner_id=5)],
            lobby_config=[],
        ))
        assert service.find_lobby_details("abc") is None

    def test_returns_none_for_an_unknown_lobby_id(self):
        service = LobbyService(make_state())
        assert service.find_lobby_details("nonexistent") is None


class TestConnectionsForLobby:
    def test_returns_only_connections_for_the_given_lobby(self):
        service = LobbyService(make_state(connection=[
            Connection(lobby_id="abc", guild_name="Server A", channel_id=1, webhook="w", guild_id=1),
            Connection(lobby_id="abc", guild_name="Server B", channel_id=2, webhook="w", guild_id=2),
            Connection(lobby_id="other", guild_name="Server C", channel_id=3, webhook="w", guild_id=3),
        ]))
        result = service.connections_for_lobby("abc")
        assert [c.guild_name for c in result] == ["Server A", "Server B"]


class TestHasRoom:
    def test_true_when_under_the_limit(self):
        service = LobbyService(make_state(connection=[Connection(lobby_id="abc", channel_id=1, webhook="w", guild_id=1, guild_name="A")]))
        assert service.has_room(LobbyView(lobby_id="abc", guild_id=1, title="t", description="d", topics=[], limit=2)) is True

    def test_false_when_at_the_limit(self):
        service = LobbyService(make_state(connection=[
            Connection(lobby_id="abc", channel_id=1, webhook="w", guild_id=1, guild_name="A"),
            Connection(lobby_id="abc", channel_id=2, webhook="w", guild_id=1, guild_name="A"),
        ]))
        assert service.has_room(LobbyView(lobby_id="abc", guild_id=1, title="t", description="d", topics=[], limit=2)) is False


class TestListLobbySummaries:
    def test_joins_lobby_data_and_config_with_live_connection_counts(self):
        state = make_state(
            lobby_data=[Lobby(lobby_id="abc", guild_id=1, guild_name="A", owner_id=5)],
            lobby_config=[LobbyConfig(lobby_id="abc", lobby_config=LobbyDetails(title="My Lobby", description="desc", topics=["a"], limit=20))],
            connection=[
                Connection(lobby_id="abc", channel_id=1, webhook="w", guild_id=1, guild_name="A"),
                Connection(lobby_id="abc", channel_id=2, webhook="w", guild_id=1, guild_name="A"),
            ],
        )
        summaries = LobbyService(state).list_lobby_summaries()
        assert summaries == [LobbyView(
            lobby_id="abc", guild_id=1, title="My Lobby", description="desc",
            topics=["a"], limit=20, connection_count=2,
        )]

    def test_skips_lobbies_missing_a_config(self):
        state = make_state(lobby_data=[Lobby(lobby_id="orphaned", guild_id=1, guild_name="A", owner_id=5)], lobby_config=[])
        assert LobbyService(state).list_lobby_summaries() == []


class TestCreateLobby:
    def test_persists_and_caches_lobby_and_config(self):
        state = make_state()
        repo = FakeRepository()
        service = LobbyService(state, repo)

        result = asyncio.run(service.create_lobby(
            lobby_id="abc", guild_id=1, guild_name="Server A", owner_id=5,
            title="My Lobby", description="A place to chat", topics=["gaming"],
        ))

        assert result == Lobby(guild_id=1, guild_name="Server A", lobby_id="abc", owner_id=5, _id="fake-id")
        assert result in state.lobby_data
        assert repo.lobby_repository.created == [result]

        assert len(state.lobby_config) == 1
        config = state.lobby_config[0]
        assert config.lobby_id == "abc"
        assert config.lobby_config.title == "My Lobby"
        assert config.lobby_config.topics == ["gaming"]
        assert config.moderation_config.banned_server == []
        assert repo.lobby_config_repository.created == [config]
