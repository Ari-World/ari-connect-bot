import logging
from typing import Optional
import motor
from motor.motor_asyncio import AsyncIOMotorClient

from .. import errors
from ..data_mananger import getDBUrl,load_basic_configuration

#  All Collections
#   #globalmarket = db['globalmarket']
#   guilds_collection = db['open_world']
#   muted_collection = db['muted_world_users']
#   lobby_collection = db['lobbies']
#   malurl_collection = db['malicious_urls']
#   malword_collection = db['malicious_words']
log = logging.getLogger("driver.mongo")

load_basic_configuration()
cluster = AsyncIOMotorClient([getDBUrl()])

class StaticDatabase:
  db = cluster['AriConnectDB']
  #globalmarket = db['globalmarket']
  guilds_collection = db['open_world']
  muted_collection = db['muted_world_users']
  lobby_collection = db['lobbies']
  malurl_collection = db['malicious_urls']
  malword_collection = db['malicious_words']


class MongoDriver:

    _conn: Optional["motor.motor_asyncio.AsyncIOMotorClient"] = None
    @classmethod
    async def initialize(cls) -> None:
        if motor is None:
            raise errors.MissingExtraRequirements(
                "Ari must be installed with the [mongo] extra to use the MongoDB driver"
            )
        url = getDBUrl()

        cls._conn = AsyncIOMotorClient(url, retryWrites=True)
        log.info("MongoDB has been initialize")
    @classmethod
    async def teardown(cls) -> None:
        if cls._conn is not None:
            cls._conn.close()
    
    @property
    def db(self) -> "motor.core.Database":
        """
        Gets the mongo database for this cog's name.

        :return:
            PyMongo Database object.
        """
        return self._conn.get_database()

    def get_collection(self, collection: str) -> "motor.core.Collection":
        """
        Gets a specified collection within the PyMongo database for this cog.

        Unless you are doing custom stuff ``category`` should be one of the class
        attributes of :py:class:`core.config.Config`.

        :param str category:
            The group identifier of a category.
        :return:
            PyMongo collection object.
        """
        return self.db[collection]