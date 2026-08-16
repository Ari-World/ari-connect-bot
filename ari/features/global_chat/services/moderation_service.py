"""Moderation business logic: permission levels, malicious-content
detection, the mute list, banned word/link lists, and moderator role
management.

Deliberately **global** — one set of moderators/mutes/banned words across
the whole bot, not per-lobby. That matches what's been live for customers
since the first deployment; per-lobby moderation (the `moderation_config`
scaffold already sitting unused in `lobby_config`) is a separate future
decision, not something this service or its callers should assume.
"""
from typing import List, Optional, Tuple

from ..domain.models import BannedContent, ModeratorAssignment, ModeratorRole, MutedUser
from ..persistence.state import GlobalChatState


class ModerationService:
    def __init__(self, state: GlobalChatState, repository=None):
        self.state = state
        self.repos = repository

    def get_user_level(self, user_id: int) -> int:
        return self.state.get_user_level(user_id)

    def is_authorized(self, user_id: int, required_level: int) -> bool:
        """True if `user_id` may run a command gated at `required_level`.

        Level 0 (not a configured moderator) is always denied. Otherwise,
        lower level numbers are more senior — a moderator may run a
        command if their own level is <= the level it requires.

        This replaces the confirmed-inverted original check
        (`user_level >= required_level + 1` → deny), which let every
        non-moderator through and denied senior moderators access to
        lower-numbered (higher-privilege) commands.
        """
        user_level = self.get_user_level(user_id)
        return user_level != 0 and user_level <= required_level

    def contains_malicious_content(self, content: str) -> Tuple[bool, Optional[str]]:
        return self.state.contains_malicious_url(content)

    def is_user_muted(self, user_id: int) -> Optional[MutedUser]:
        return self.state.isUserBlackListed(user_id)

    async def mute_user(self, user_id: int, user_name: str, reason: str, muted_by: str) -> MutedUser:
        muted_user = MutedUser(id=user_id, name=user_name, reason=reason, mutedBy=muted_by)
        await self.repos.muted_repository.create(muted_user)
        self.state.muted_users.append(muted_user)
        return muted_user

    async def unmute_user(self, user_id: int) -> Optional[MutedUser]:
        existing = next((muted_user for muted_user in self.state.muted_users if muted_user.id == user_id), None)
        if not existing:
            return None
        await self.repos.muted_repository.delete(existing.id)
        self.state.muted_users.remove(existing)
        return existing

    async def add_banned_url(self, content: str) -> None:
        entity = BannedContent(content=content)
        self.state.malicious_urls.append(entity)
        await self.repos.malicious_urls_repository.create(content)

    async def remove_banned_url(self, content: str) -> Optional[BannedContent]:
        existing = await self.repos.malicious_urls_repository.findOne(content)
        if not existing:
            return None
        await self.repos.malicious_urls_repository.delete(content)
        self.state.malicious_urls = [url for url in self.state.malicious_urls if url.content != content]
        return existing

    async def add_banned_word(self, content: str) -> None:
        entity = BannedContent(content=content)
        self.state.malicious_words.append(entity)
        await self.repos.malicious_words_repository.create(content)

    async def remove_banned_word(self, content: str) -> Optional[BannedContent]:
        existing = await self.repos.malicious_words_repository.findOne(content)
        if not existing:
            return None
        await self.repos.malicious_words_repository.delete(content)
        self.state.malicious_words = [word for word in self.state.malicious_words if word.content != content]
        return existing

    def find_role_level(self, level) -> Optional[ModeratorRole]:
        return next((role for role in self.state.moderator if role.level == level), None)

    def find_role_by_user(self, user_id) -> Optional[ModeratorRole]:
        return next((role for role in self.state.moderator if any(mod.user_id == user_id for mod in role.mods)), None)

    async def assign_role(self, level, user_id, name, lobby_name) -> bool:
        """Adds a moderator to an existing role level. Callers are expected
        to have already confirmed the level exists and the user isn't
        already assigned — this only does the write."""
        role = self.find_role_level(level)
        if not role:
            return False
        updated_mods = role.mods + [ModeratorAssignment(user_id=user_id, name=name, lobby_name=lobby_name)]
        updated_role = ModeratorRole(role_name=role.role_name, icon=role.icon, level=level, mods=updated_mods)
        updated = await self.repos.moderator_repository.update(updated_role)
        if updated:
            role.mods = updated_mods
        return bool(updated)

    async def create_role(self, level, role_name, icon) -> bool:
        if self.find_role_level(level):
            return False
        role = ModeratorRole(role_name=role_name, icon=str(icon), level=level, mods=[])
        created = await self.repos.moderator_repository.create(role)
        if created:
            self.state.moderator.append(role)
        return bool(created)

    async def remove_role(self, user_id) -> bool:
        role = self.find_role_by_user(user_id)
        if not role:
            return False
        updated_mods = [mod for mod in role.mods if mod.user_id != user_id]
        updated_role = ModeratorRole(role_name=role.role_name, icon=role.icon, level=role.level, mods=updated_mods)
        updated = await self.repos.moderator_repository.update(updated_role)
        if updated:
            role.mods = updated_mods
        return bool(updated)
