from motor.motor_asyncio import AsyncIOMotorClient


cluster = AsyncIOMotorClient(['mongodb+srv://ajrizaldo1:NeWW90S4YyOF9Kp2@cluster0.uw5p0nu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'])

class db:
  db = cluster['AriDB']
  #globalmarket = db['globalmarket']
  guilds_collection = db['open_world']
  muted_collection = db['muted_world_users']