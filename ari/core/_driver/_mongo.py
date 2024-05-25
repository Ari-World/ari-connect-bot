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
  guilds_collection = db['open_world']
  muted_collection = db['muted_world_users']
  lobby_collection = db['lobbies']
  malurl_collection = db['malicious_urls']
  malword_collection = db['malicious_words']

async def close_db_connection():
    cluster.close()