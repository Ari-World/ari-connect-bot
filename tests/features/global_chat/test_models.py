"""Round-trip tests for the domain layer's dict <-> dataclass boundary.
Nested shapes (LobbyConfig, ModeratorRole) are the most likely place a
mapping mistake would hide, since a typo in a nested key wouldn't show up
until something tries to read that specific field.
"""
from features.global_chat.domain.models import (
    BannedContent,
    Connection,
    Lobby,
    LobbyConfig,
    LobbyDetails,
    LogChannel,
    LogConfig,
    ModerationConfig,
    ModeratorAssignment,
    ModeratorRole,
    MutedUser,
)


def test_lobby_round_trip():
    lobby = Lobby(lobby_id="abc", guild_id=1, guild_name="Server", owner_id=5, _id="oid")
    assert Lobby.from_document(lobby.to_document()) == lobby


def test_connection_round_trip():
    connection = Connection(lobby_id="abc", channel_id=10, webhook="url", guild_id=1, guild_name="Server", _id="oid")
    assert Connection.from_document(connection.to_document()) == connection


def test_muted_user_round_trip():
    muted = MutedUser(id=1, name="Bad Actor", reason="spam", mutedBy="ModName")
    assert MutedUser.from_document(muted.to_document()) == muted


def test_banned_content_round_trip():
    banned = BannedContent(content="bad.example")
    assert BannedContent.from_document(banned.to_document()) == banned


def test_lobby_config_round_trip_including_nested_fields():
    config = LobbyConfig(
        lobby_id="abc",
        lobby_config=LobbyDetails(title="My Lobby", description="desc", topics=["a", "b"], limit=20, footer="f"),
        moderation_config=ModerationConfig(moderators=["1"], banned_words=["bad"], banned_links=["x"], banned_users=["2"], banned_server=["3"]),
        log_config=LogConfig(
            chat_log=LogChannel(guild_id=1, channel_id=2),
            moderation_log=LogChannel(guild_id=3, channel_id=4),
            report_logs=LogChannel(guild_id=5, channel_id=6),
        ),
        _id="oid",
    )
    round_tripped = LobbyConfig.from_document(config.to_document())
    assert round_tripped == config
    # Specifically lock in the two schema keys that were confirmed bugs
    # before (singular "banned_server", singular "moderation_log") —
    # a document with the wrong key would silently produce empty defaults
    # here instead of failing loudly.
    assert round_tripped.moderation_config.banned_server == ["3"]
    assert round_tripped.log_config.moderation_log.channel_id == 4


def test_lobby_config_from_document_defaults_missing_nested_sections():
    # A lobby created before moderation_config/log_config existed (or a
    # partially-written document) shouldn't crash — it should default.
    doc = {"lobby_id": "abc", "lobby_config": {"title": "t", "description": "d", "limit": 20}}
    config = LobbyConfig.from_document(doc)
    assert config.moderation_config == ModerationConfig()
    assert config.log_config == LogConfig()


def test_moderator_role_round_trip_including_mods_list():
    role = ModeratorRole(
        role_name="Mod", icon="🛡️", level="1",
        mods=[
            ModeratorAssignment(user_id="42", name="A", lobby_name="ALL"),
            ModeratorAssignment(user_id="99", name="B", lobby_name="ALL"),
        ],
    )
    round_tripped = ModeratorRole.from_document(role.to_document())
    assert round_tripped == role
    assert len(round_tripped.mods) == 2
