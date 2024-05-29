import logging
from motor.motor_asyncio import AsyncIOMotorClient

from ..data_mananger import getDBUrl

#  All Collections
#   #globalmarket = db['globalmarket']
#   guilds_collection = db['open_world']
#   muted_collection = db['muted_world_users']
#   lobby_collection = db['lobbies']
#   malurl_collection = db['malicious_urls']
#   malword_collection = db['malicious_words']
log = logging.getLogger("driver.mongo")


class StaticDatabase:

    _cluster = None
    _db = None

    @classmethod
    def get_db(cls):
        if cls._db is None:
            cls._connect()
        return cls._db
    
    @classmethod
    def _connect(cls):
        log.info("Establishing new database connection.")
        cls._cluster = AsyncIOMotorClient(getDBUrl())
        cls._db = cls._cluster['AriConnectDB']

    @classmethod
    async def close_db_connection(cls):
        if cls._cluster is not None:
            log.info("Closing database connection.")
            cls._cluster.close()
            cls._cluster = None
            cls._db = None

    @classmethod
    def guilds_collection(cls):
        return cls.get_db()['open_world']

    @classmethod
    def muted_collection(cls):
        return cls.get_db()['muted_world_users']

    @classmethod
    def lobby_collection(cls):
        return cls.get_db()['lobbies']

    @classmethod
    def malurl_collection(cls):
        return cls.get_db()['malicious_urls']

    @classmethod
    def malword_collection(cls):
        return cls.get_db()['malicious_words']
        
    @classmethod
    def moderator_collection(cls):
        return cls.get_db()["moderators"]