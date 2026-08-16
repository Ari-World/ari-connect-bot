"""Unit tests for GlobalChatState's pure query helpers.

These construct a bare `GlobalChatState` (bypassing `__init__`, which needs
a live bot + loaded config) and set only the attributes each method reads,
per the PRD's testing seam: plain-function business logic, no Discord
connection or database required.
"""
from features.global_chat.domain.models import BannedContent, Connection, ModeratorAssignment, ModeratorRole, MutedUser
from features.global_chat.persistence.state import GlobalChatState


def make_state(**attrs) -> GlobalChatState:
    state = GlobalChatState.__new__(GlobalChatState)
    for key, value in attrs.items():
        setattr(state, key, value)
    return state


class TestContainsMaliciousUrl:
    def test_matches_a_banned_url_pattern(self):
        state = make_state(
            malicious_urls=[BannedContent(content=r"badsite\.com")],
            malicious_words=[BannedContent(content="spamword")],
        )
        found, matched = state.contains_malicious_url("check out http://badsite.com/x")
        assert found is True
        assert matched == r"badsite\.com"

    def test_matches_a_banned_word_case_insensitively(self):
        state = make_state(
            malicious_urls=[BannedContent(content=r"badsite\.com")],
            malicious_words=[BannedContent(content="spamword")],
        )
        found, matched = state.contains_malicious_url("this message has SpamWord in it")
        assert found is True
        assert matched == "spamword"

    def test_no_match_returns_false_and_none(self):
        state = make_state(
            malicious_urls=[BannedContent(content=r"badsite\.com")],
            malicious_words=[BannedContent(content="spamword")],
        )
        found, matched = state.contains_malicious_url("a perfectly normal message")
        assert found is False
        assert matched is None

    def test_empty_lists_never_match(self):
        state = make_state(malicious_urls=[], malicious_words=[])
        found, matched = state.contains_malicious_url("badsite.com spamword")
        assert found is False
        assert matched is None


class TestIsUserBlackListed:
    def test_finds_a_muted_user(self):
        muted = MutedUser(id=111, name="Bad Actor", reason="spam")
        state = make_state(muted_users=[muted])
        assert state.isUserBlackListed(111) == muted

    def test_returns_none_for_a_user_not_muted(self):
        state = make_state(muted_users=[MutedUser(id=111, name="Bad Actor", reason="spam")])
        assert state.isUserBlackListed(222) is None

    def test_returns_none_when_no_one_is_muted(self):
        state = make_state(muted_users=[])
        assert state.isUserBlackListed(111) is None


class TestGetUserLevel:
    def test_returns_configured_level_for_a_moderator(self):
        state = make_state(moderator=[
            ModeratorRole(role_name="Mod", icon="x", level="1", mods=[ModeratorAssignment(user_id="42", name="n", lobby_name="ALL")]),
            ModeratorRole(role_name="Mod", icon="x", level="3", mods=[ModeratorAssignment(user_id="99", name="n", lobby_name="ALL")]),
        ])
        assert state.get_user_level(42) == 1
        assert state.get_user_level(99) == 3

    def test_returns_zero_for_a_non_moderator(self):
        state = make_state(moderator=[
            ModeratorRole(role_name="Mod", icon="x", level="1", mods=[ModeratorAssignment(user_id="42", name="n", lobby_name="ALL")]),
        ])
        assert state.get_user_level(12345) == 0

    def test_returns_zero_when_there_are_no_moderators(self):
        state = make_state(moderator=[])
        assert state.get_user_level(42) == 0


class TestGetLobbyLength:
    def test_counts_connections_for_the_given_lobby(self):
        state = make_state(connection=[
            Connection(lobby_id="abc123", channel_id=1, webhook="w", guild_id=1, guild_name="A"),
            Connection(lobby_id="abc123", channel_id=2, webhook="w", guild_id=2, guild_name="B"),
            Connection(lobby_id="other", channel_id=3, webhook="w", guild_id=3, guild_name="C"),
        ])
        assert state.get_lobby_length("abc123") == 2

    def test_returns_zero_for_a_lobby_with_no_connections(self):
        state = make_state(connection=[Connection(lobby_id="abc123", channel_id=1, webhook="w", guild_id=1, guild_name="A")])
        assert state.get_lobby_length("nonexistent") == 0
