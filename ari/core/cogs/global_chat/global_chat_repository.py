
import logging

import discord 
from discord.ext import commands
log = logging.getLogger("globalchat.repository")
from ..._driver._mongo import StaticDatabase


class Repository:
    def __init__(self):
        self.db = StaticDatabase
        
        self.startDatabase()

    def startDatabase(self):
        self.guild_repository = GuildConnectionRepository(self.db)
        self.lobby_repository = LobbyRepository(self.db)
        self.lobby_config_repository = LobbyConfigurationRepository(self.db)

class LobbyConfigurationRepository():
    def __init__(self,db) -> None:
        self.collection = db.lobby_config_collection()
    
    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,lobby_id):
        return await self.collection.find_one({'lobby_id':lobby_id})
    
    async def create(self, data):
        res = await self.collection.insert_one(data)
        return res
    
    async def delete(self, data):
        return await self.collection.delete_one({
            "lobby_id": data["lobby_id"],
        })

        
class LobbyRepository():
    def __init__(self,db):
        self.collection = db.lobby_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,lobby_id):
        return await self.collection.find_one({"lobby_id":lobby_id})
    
    async def create(self, data):
        res = await self.collection.insert_one(data)
        return res
    
    async def delete(self,data):
        return await self.collection.delete_one({
            "lobby_id": data["lobby_id"],
        })

class GuildConnectionRepository():
    def __init__(self, db):
        self.collection = db.guilds_collection()

    async def findFilter(self, filter):
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=None)
    
    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self, lobby_id):
        return await self.collection.find_one({"lobby_id": lobby_id})

    async def create(self, data):
        res =  await self.collection.insert_one(data) 
        return res
    
    async def delete(self,data):
        await self.collection.delete_one({"lobby_id": data["lobby_id"],"channel_id": data['channel_id']})  # Delete the guild document
        
         
        
    async def update(self,data):
        if await self.findOne(data["server_id"]):  
            result = await self.collection.update_one(
                {"server_id": data["server_id"]},
                {"$set": {"channels": data["channels"]}}
            ) 
            return result.modified_count > 0
        else:
            return None  

class ModeratorRepository():
    def __init__(self, db):
        self.collection = db.moderator_collection()

    async def findFilter(self, filter):
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=None)
    
    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self, user_id):
        return await self.collection.find_one({"level": user_id})

    async def create(self, data):
        if await self.findOne(data["level"]):  
            return None
        try:
            await self.collection.insert_one({
                "role_name": data["role_name"],
                "icon": data["icon"],
                "level": data["level"],
                "mods": data["mods"]
            }) 
            return True 
        except:
            return False

    async def delete(self,data):
        if await self.findOne(data["level"]):  
            await self.collection.delete_one({"level": data["level"]})  # Delete the guild document
            return True
        else:
            return False  
        
    async def update(self,data):
        if await self.findOne(data["level"]):  
            result = await self.collection.update_one(
                {"level": data["level"]},
                {"$set": {"mods": data["mods"]}}
            ) 
            return result.modified_count > 0
        else:
            return None