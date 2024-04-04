from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(['mongodb+srv://worlddb:wa45GQZ0ZDNm8mDL@worlddb.vxc5i0q.mongodb.net/?retryWrites=true&w=majority'])

class db:
  db = cluster['AriToramDB']
  globalmarket = db['globalmarket']
  guilds_collection = db['open_world']
  muted_collection = db['muted_world_users']