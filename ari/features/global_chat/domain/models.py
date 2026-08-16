"""The domain layer: typed shapes for every document global_chat persists.

Before this existed, every collection was a raw dict shaped by whatever a
`create()` call happened to pass in — there was no single place that said
"here's what a lobby looks like," and a typo'd field name would silently
produce a `KeyError` somewhere downstream instead of failing at the point
of the mistake. `repository.py` is the only place that talks dict (Mongo
documents) — everything above it works with these dataclasses.

Each type has `to_document()`/`from_document()` for the dict <-> dataclass
boundary. Mutable (not frozen) on purpose — `state.py` and the services
append/remove/mutate these in place, the same way the old dict-based
lists worked.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Lobby:
    """A lobby's identity — who owns it and which guild created it. Display
    info (title/description/topics/limit) lives in `LobbyConfig` instead;
    the two are separate collections that get joined by `lobby_id`."""
    lobby_id: str
    guild_id: int
    guild_name: str
    owner_id: int
    _id: Optional[object] = None

    def to_document(self) -> dict:
        doc = {"lobby_id": self.lobby_id, "guild_id": self.guild_id, "guild_name": self.guild_name, "owner_id": self.owner_id}
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    @classmethod
    def from_document(cls, doc: dict) -> "Lobby":
        return cls(
            lobby_id=doc["lobby_id"],
            guild_id=doc["guild_id"],
            guild_name=doc["guild_name"],
            owner_id=doc["owner_id"],
            _id=doc.get("_id"),
        )


@dataclass
class LobbyDetails:
    title: str
    description: str
    topics: List[str] = field(default_factory=list)
    limit: int = 20
    footer: str = ""

    def to_document(self) -> dict:
        return {"title": self.title, "description": self.description, "topics": self.topics, "limit": self.limit, "footer": self.footer}

    @classmethod
    def from_document(cls, doc: dict) -> "LobbyDetails":
        return cls(
            title=doc["title"],
            description=doc["description"],
            topics=doc.get("topics", []),
            limit=doc["limit"],
            footer=doc.get("footer", ""),
        )


@dataclass
class ModerationConfig:
    """The per-lobby moderation scaffold — unwired, see settings_commands.py."""
    moderators: List[str] = field(default_factory=list)
    banned_words: List[str] = field(default_factory=list)
    banned_links: List[str] = field(default_factory=list)
    banned_users: List[str] = field(default_factory=list)
    banned_server: List[str] = field(default_factory=list)

    def to_document(self) -> dict:
        return {
            "moderators": self.moderators, "banned_words": self.banned_words, "banned_links": self.banned_links,
            "banned_users": self.banned_users, "banned_server": self.banned_server,
        }

    @classmethod
    def from_document(cls, doc: dict) -> "ModerationConfig":
        return cls(
            moderators=doc.get("moderators", []), banned_words=doc.get("banned_words", []),
            banned_links=doc.get("banned_links", []), banned_users=doc.get("banned_users", []),
            banned_server=doc.get("banned_server", []),
        )


@dataclass
class LogChannel:
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None

    def to_document(self) -> dict:
        return {"guild_id": self.guild_id, "channel_id": self.channel_id}

    @classmethod
    def from_document(cls, doc: dict) -> "LogChannel":
        return cls(guild_id=doc.get("guild_id"), channel_id=doc.get("channel_id"))


@dataclass
class LogConfig:
    """Also unwired — see `ModerationConfig`."""
    chat_log: LogChannel = field(default_factory=LogChannel)
    moderation_log: LogChannel = field(default_factory=LogChannel)
    report_logs: LogChannel = field(default_factory=LogChannel)

    def to_document(self) -> dict:
        return {"chat_log": self.chat_log.to_document(), "moderation_log": self.moderation_log.to_document(), "report_logs": self.report_logs.to_document()}

    @classmethod
    def from_document(cls, doc: dict) -> "LogConfig":
        return cls(
            chat_log=LogChannel.from_document(doc.get("chat_log", {})),
            moderation_log=LogChannel.from_document(doc.get("moderation_log", {})),
            report_logs=LogChannel.from_document(doc.get("report_logs", {})),
        )


@dataclass
class LobbyConfig:
    lobby_id: str
    lobby_config: LobbyDetails
    moderation_config: ModerationConfig = field(default_factory=ModerationConfig)
    log_config: LogConfig = field(default_factory=LogConfig)
    _id: Optional[object] = None

    def to_document(self) -> dict:
        doc = {
            "lobby_id": self.lobby_id,
            "lobby_config": self.lobby_config.to_document(),
            "moderation_config": self.moderation_config.to_document(),
            "log_config": self.log_config.to_document(),
        }
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    @classmethod
    def from_document(cls, doc: dict) -> "LobbyConfig":
        return cls(
            lobby_id=doc["lobby_id"],
            lobby_config=LobbyDetails.from_document(doc["lobby_config"]),
            moderation_config=ModerationConfig.from_document(doc.get("moderation_config", {})),
            log_config=LogConfig.from_document(doc.get("log_config", {})),
            _id=doc.get("_id"),
        )


@dataclass
class Connection:
    """One connected channel. Note: one record per *channel*, not per guild
    — a server with two connected channels has two Connection records."""
    lobby_id: str
    channel_id: int
    webhook: str
    guild_id: int
    guild_name: str
    _id: Optional[object] = None

    def to_document(self) -> dict:
        doc = {"lobby_id": self.lobby_id, "channel_id": self.channel_id, "webhook": self.webhook, "guild_id": self.guild_id, "guild_name": self.guild_name}
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    @classmethod
    def from_document(cls, doc: dict) -> "Connection":
        return cls(
            lobby_id=doc["lobby_id"],
            channel_id=doc["channel_id"],
            webhook=doc["webhook"],
            guild_id=doc["guild_id"],
            guild_name=doc["guild_name"],
            _id=doc.get("_id"),
        )


@dataclass
class LobbyView:
    """A `Lobby` and its `LobbyConfig` joined into one read-only view — what
    `/current`, `/lobby_show`, `/connect`, `/switch`, and `/lobbies` all
    actually want. Not persisted itself; `LobbyService.find_lobby_details`
    builds this from the two separate collections it's named after."""
    lobby_id: str
    guild_id: int
    title: str
    description: str
    topics: List[str]
    limit: int
    footer_message: str = ""
    connection_count: int = 0
    """Only populated by `LobbyService.list_lobby_summaries` (for the
    `/lobbies` pagination view) — 0 everywhere else. Callers that need the
    live count in other contexts get it from `connections_for_lobby`."""


@dataclass
class MutedUser:
    id: int
    name: str
    reason: str
    mutedBy: str = ""

    def to_document(self) -> dict:
        return {"id": self.id, "name": self.name, "reason": self.reason, "mutedBy": self.mutedBy}

    @classmethod
    def from_document(cls, doc: dict) -> "MutedUser":
        return cls(id=doc["id"], name=doc["name"], reason=doc["reason"], mutedBy=doc.get("mutedBy", ""))


@dataclass
class BannedContent:
    """Shared shape for both `malicious_urls` and `malicious_words` — same
    single field either way."""
    content: str

    def to_document(self) -> dict:
        return {"content": self.content}

    @classmethod
    def from_document(cls, doc: dict) -> "BannedContent":
        return cls(content=doc["content"])


@dataclass
class ModeratorAssignment:
    user_id: str
    name: str
    lobby_name: str

    def to_document(self) -> dict:
        return {"user_id": self.user_id, "name": self.name, "lobby_name": self.lobby_name}

    @classmethod
    def from_document(cls, doc: dict) -> "ModeratorAssignment":
        return cls(user_id=doc["user_id"], name=doc["name"], lobby_name=doc["lobby_name"])


@dataclass
class ModeratorRole:
    """One record per permission *level*, not per moderator — `mods` is the
    list of everyone assigned to that level."""
    role_name: str
    icon: str
    level: str
    mods: List[ModeratorAssignment] = field(default_factory=list)

    def to_document(self) -> dict:
        return {"role_name": self.role_name, "icon": self.icon, "level": self.level, "mods": [mod.to_document() for mod in self.mods]}

    @classmethod
    def from_document(cls, doc: dict) -> "ModeratorRole":
        return cls(
            role_name=doc["role_name"],
            icon=doc["icon"],
            level=doc["level"],
            mods=[ModeratorAssignment.from_document(mod) for mod in doc.get("mods", [])],
        )
