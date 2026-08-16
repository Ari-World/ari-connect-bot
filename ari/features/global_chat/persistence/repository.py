"""Pure CRUD, one class per MongoDB collection. Every method takes/returns
the typed shapes from `models.py` — this is the only file that converts
between those and raw Mongo documents (via each model's `to_document()`/
`from_document()`). No cache mutation, no Discord API calls.
"""
import logging
from typing import List, Optional

from core._driver._mongo import StaticDatabase

from ..domain.models import BannedContent, Connection, Lobby, LobbyConfig, ModeratorRole, MutedUser

log = logging.getLogger("globalchat.repository")


class Repository:
    def __init__(self):
        self.db = StaticDatabase

        self.startDatabase()

    def startDatabase(self):
        self.guild_repository = GuildConnectionRepository(self.db)
        self.lobby_repository = LobbyRepository(self.db)
        self.lobby_config_repository = LobbyConfigurationRepository(self.db)
        self.muted_repository = MutedRepository(self.db)
        self.malicious_urls_repository = MaliciousURLRepository(self.db)
        self.malicious_words_repository = MaliciousWordsRepository(self.db)
        self.moderator_repository = ModeratorRepository(self.db)


class LobbyConfigurationRepository():
    def __init__(self, db) -> None:
        self.collection = db.lobby_config_collection()

    async def findAll(self) -> List[LobbyConfig]:
        cursor = self.collection.find()
        return [LobbyConfig.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, lobby_id) -> Optional[LobbyConfig]:
        doc = await self.collection.find_one({'lobby_id': lobby_id})
        return LobbyConfig.from_document(doc) if doc else None

    async def create(self, config: LobbyConfig) -> LobbyConfig:
        res = await self.collection.insert_one(config.to_document())
        config._id = res.inserted_id
        return config

    async def delete(self, config: LobbyConfig):
        return await self.collection.delete_one({
            "lobby_id": config.lobby_id,
        })


class LobbyRepository():
    def __init__(self, db):
        self.collection = db.lobby_collection()

    async def findAll(self) -> List[Lobby]:
        cursor = self.collection.find()
        return [Lobby.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, lobby_id) -> Optional[Lobby]:
        doc = await self.collection.find_one({"lobby_id": lobby_id})
        return Lobby.from_document(doc) if doc else None

    async def create(self, lobby: Lobby) -> Lobby:
        res = await self.collection.insert_one(lobby.to_document())
        lobby._id = res.inserted_id
        return lobby

    async def delete(self, lobby: Lobby):
        return await self.collection.delete_one({
            "lobby_id": lobby.lobby_id,
        })


class GuildConnectionRepository():
    def __init__(self, db):
        self.collection = db.guilds_collection()

    async def findFilter(self, filter) -> List[Connection]:
        cursor = self.collection.find(filter)
        return [Connection.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findAll(self) -> List[Connection]:
        cursor = self.collection.find()
        return [Connection.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, lobby_id) -> Optional[Connection]:
        doc = await self.collection.find_one({"lobby_id": lobby_id})
        return Connection.from_document(doc) if doc else None

    async def create(self, connection: Connection) -> Connection:
        res = await self.collection.insert_one(connection.to_document())
        connection._id = res.inserted_id
        return connection

    async def delete(self, connection: Connection):
        await self.collection.delete_one({"lobby_id": connection.lobby_id, "channel_id": connection.channel_id})

    async def update(self, connection: Connection):
        # Kept for interface completeness — not currently called anywhere;
        # connect/unlink/switch delete + recreate rather than update in place.
        if await self.findOne(connection.lobby_id):
            result = await self.collection.update_one(
                {"lobby_id": connection.lobby_id, "channel_id": connection.channel_id},
                {"$set": connection.to_document()}
            )
            return result.modified_count > 0
        else:
            return None


class MutedRepository():
    def __init__(self, db):
        self.collection = db.muted_collection()

    async def findAll(self) -> List[MutedUser]:
        cursor = self.collection.find()
        return [MutedUser.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, id) -> Optional[MutedUser]:
        doc = await self.collection.find_one({"id": id})
        return MutedUser.from_document(doc) if doc else None

    async def create(self, muted_user: MutedUser) -> MutedUser:
        await self.collection.insert_one(muted_user.to_document())
        return muted_user

    async def delete(self, id):
        return await self.collection.delete_one({
            "id": id,
        })


class MaliciousURLRepository():
    def __init__(self, db):
        self.collection = db.malurl_collection()

    async def findAll(self) -> List[BannedContent]:
        cursor = self.collection.find()
        return [BannedContent.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, content: str) -> Optional[BannedContent]:
        doc = await self.collection.find_one({"content": content})
        return BannedContent.from_document(doc) if doc else None

    async def create(self, content: str) -> Optional[BannedContent]:
        if await self.findOne(content):
            return None
        entity = BannedContent(content=content)
        await self.collection.insert_one(entity.to_document())
        return entity

    async def delete(self, content: str):
        if await self.findOne(content):
            return await self.collection.delete_one({
                "content": content
            })
        else:
            return None


class MaliciousWordsRepository():
    def __init__(self, db):
        self.collection = db.malword_collection()

    async def findAll(self) -> List[BannedContent]:
        cursor = self.collection.find()
        return [BannedContent.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, content: str) -> Optional[BannedContent]:
        doc = await self.collection.find_one({"content": content})
        return BannedContent.from_document(doc) if doc else None

    async def create(self, content: str) -> Optional[BannedContent]:
        if await self.findOne(content):
            return None
        entity = BannedContent(content=content)
        await self.collection.insert_one(entity.to_document())
        return entity

    async def delete(self, content: str):
        return await self.collection.delete_one({
            "content": content
        })


class ModeratorRepository():
    def __init__(self, db):
        self.collection = db.moderator_collection()

    async def findFilter(self, filter) -> List[ModeratorRole]:
        cursor = self.collection.find(filter)
        return [ModeratorRole.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findAll(self) -> List[ModeratorRole]:
        cursor = self.collection.find()
        return [ModeratorRole.from_document(doc) for doc in await cursor.to_list(length=None)]

    async def findOne(self, level) -> Optional[ModeratorRole]:
        doc = await self.collection.find_one({"level": level})
        return ModeratorRole.from_document(doc) if doc else None

    async def create(self, role: ModeratorRole) -> bool:
        if await self.findOne(role.level):
            return None
        try:
            await self.collection.insert_one(role.to_document())
            return True
        except Exception:
            return False

    async def delete(self, role: ModeratorRole):
        if await self.findOne(role.level):
            await self.collection.delete_one({"level": role.level})
            return True
        else:
            return False

    async def update(self, role: ModeratorRole):
        if await self.findOne(role.level):
            result = await self.collection.update_one(
                {"level": role.level},
                {"$set": {"mods": [mod.to_document() for mod in role.mods]}}
            )
            return result.modified_count > 0
        else:
            return None
