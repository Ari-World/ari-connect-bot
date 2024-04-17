from motor.motor_asyncio import AsyncIOMotorClient
from plugins import config

config = config.load_config()
cluster = AsyncIOMotorClient([config['MONGO_DB_URL']])

class db:
  db = cluster['AriToramDB']
  #globalmarket = db['globalmarket']
  guilds_collection = db['open_world']
  muted_collection = db['muted_world_users']
  lobby_collection = db['lobbies']
  malurl_collection = db['malicious_urls']
  malword_collection = db['malicious_words']