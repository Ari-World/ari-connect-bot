"""Unit tests for ModerationService, with explicit boundary coverage for
`is_authorized` — the fix for the confirmed inverted permission check
(issue 008). Every combination of user level (0-3) against every
required_level actually used in the cog (1, 2, 3) is covered, since the
original inversion was easy to introduce and easy to miss.
"""
import asyncio

import pytest

from features.global_chat.domain.models import BannedContent, ModeratorAssignment, ModeratorRole, MutedUser
from features.global_chat.services.moderation_service import ModerationService
from features.global_chat.persistence.state import GlobalChatState


def make_state(muted_users=None, malicious_urls=None, malicious_words=None, moderator=None):
    state = GlobalChatState.__new__(GlobalChatState)
    state.muted_users = muted_users or []
    state.malicious_urls = malicious_urls or []
    state.malicious_words = malicious_words or []
    state.moderator = moderator or []
    return state


def make_moderator_state(level, user_id):
    role = ModeratorRole(role_name="Mod", icon="x", level=str(level), mods=[ModeratorAssignment(user_id=str(user_id), name="n", lobby_name="ALL")])
    return make_state(moderator=[role])


class FakeSubRepository:
    def __init__(self):
        self.created = []
        self.deleted = []
        self.updated = []
        self._find_one_result = None

    async def create(self, data):
        self.created.append(data)
        return True

    async def delete(self, data):
        self.deleted.append(data)

    async def update(self, data):
        self.updated.append(data)
        return True

    async def findOne(self, content):
        return self._find_one_result


class FakeRepository:
    def __init__(self):
        self.muted_repository = FakeSubRepository()
        self.malicious_urls_repository = FakeSubRepository()
        self.malicious_words_repository = FakeSubRepository()
        self.moderator_repository = FakeSubRepository()


@pytest.mark.parametrize("user_level,required_level,expected", [
    # Non-moderator (level 0) is denied for every gate.
    (0, 1, False),
    (0, 2, False),
    (0, 3, False),
    # Level 1 (most senior) is authorized for every gate.
    (1, 1, True),
    (1, 2, True),
    (1, 3, True),
    # Level 2 is authorized for its own and less-senior gates, not for level 1.
    (2, 1, False),
    (2, 2, True),
    (2, 3, True),
    # Level 3 (least senior) is only authorized for the level-3 gate.
    (3, 1, False),
    (3, 2, False),
    (3, 3, True),
])
def test_is_authorized_boundary(user_level, required_level, expected):
    state = make_moderator_state(user_level, user_id=42) if user_level != 0 else make_state()
    service = ModerationService(state)
    assert service.is_authorized(42, required_level) is expected


class TestMuteUnmute:
    def test_mute_persists_and_caches(self):
        state = make_state()
        repo = FakeRepository()
        service = ModerationService(state, repo)

        result = asyncio.run(service.mute_user(1, "BadUser", "spam", "ModName"))

        assert result == MutedUser(id=1, name="BadUser", reason="spam", mutedBy="ModName")
        assert result in state.muted_users
        assert repo.muted_repository.created == [result]

    def test_unmute_removes_and_returns_the_record(self):
        state = make_state(muted_users=[MutedUser(id=1, name="BadUser", reason="spam", mutedBy="ModName")])
        repo = FakeRepository()
        service = ModerationService(state, repo)

        result = asyncio.run(service.unmute_user(1))

        assert result.id == 1
        assert state.muted_users == []
        assert repo.muted_repository.deleted == [1]

    def test_unmute_returns_none_when_not_muted(self):
        service = ModerationService(make_state(), FakeRepository())
        assert asyncio.run(service.unmute_user(999)) is None


class TestBannedContent:
    def test_add_banned_url_persists_and_caches(self):
        state = make_state()
        repo = FakeRepository()
        service = ModerationService(state, repo)

        asyncio.run(service.add_banned_url("bad.example"))

        assert BannedContent(content="bad.example") in state.malicious_urls
        assert repo.malicious_urls_repository.created == ["bad.example"]

    def test_remove_banned_url_when_present(self):
        state = make_state(malicious_urls=[BannedContent(content="bad.example")])
        repo = FakeRepository()
        repo.malicious_urls_repository._find_one_result = BannedContent(content="bad.example")
        service = ModerationService(state, repo)

        result = asyncio.run(service.remove_banned_url("bad.example"))

        assert result == BannedContent(content="bad.example")
        assert state.malicious_urls == []

    def test_remove_banned_url_when_absent_returns_none(self):
        service = ModerationService(make_state(), FakeRepository())
        assert asyncio.run(service.remove_banned_url("nonexistent")) is None


class TestRoleManagement:
    def test_find_role_level(self):
        state = make_moderator_state(1, 42)
        service = ModerationService(state)
        assert service.find_role_level("1").level == "1"
        assert service.find_role_level("99") is None

    def test_find_role_by_user(self):
        state = make_moderator_state(1, 42)
        service = ModerationService(state)
        assert service.find_role_by_user("42") is not None
        assert service.find_role_by_user("999") is None

    def test_assign_role_adds_a_moderator(self):
        state = make_state(moderator=[ModeratorRole(role_name="Mod", icon="x", level="1", mods=[])])
        repo = FakeRepository()
        service = ModerationService(state, repo)

        success = asyncio.run(service.assign_role("1", "42", "Name", "ALL"))

        assert success is True
        assert state.moderator[0].mods == [ModeratorAssignment(user_id="42", name="Name", lobby_name="ALL")]

    def test_assign_role_fails_for_unknown_level(self):
        service = ModerationService(make_state(), FakeRepository())
        assert asyncio.run(service.assign_role("99", "42", "Name", "ALL")) is False

    def test_create_role_when_level_is_new(self):
        state = make_state()
        repo = FakeRepository()
        service = ModerationService(state, repo)

        success = asyncio.run(service.create_role("2", "Helper", "🛡️"))

        assert success is True
        assert state.moderator == [ModeratorRole(role_name="Helper", icon="🛡️", level="2", mods=[])]

    def test_remove_role_removes_the_mod_entry(self):
        state = make_moderator_state(1, 42)
        repo = FakeRepository()
        service = ModerationService(state, repo)

        success = asyncio.run(service.remove_role("42"))

        assert success is True
        assert state.moderator[0].mods == []
