
import logging

import discord 

log = logging.getLogger("globalchat.repository")

class Repository:
    def __init__(self, db):
        self.guild_repository = GuildRepository(db)
        self.muted_repository = MutedRepository(db)
        self.lobby_repository = LobbyRepository(db)
        self.malicious_urls_repository = MaliciousURLRepository(db)
        self.malicious_words_repository = MaliciousWordsRepository(db)
        self.moderator_repository = ModeratorRepository(db)

        log.info("Repository Instantiated")

    async def create_guild_document(self, guild_id, channel : discord.TextChannel, server_name, lobby_name):
        """
        Create or update a guild document in the database and cache.
        
        Args:
            guild_id (int): The ID of the guild.
            channel (discord.TextChannel): The Discord text channel object.
            server_name (str): The name of the server.
            lobby_name (str): The name of the lobby.
        
        Returns:
            bool: True if the operation is successful, False otherwise.
        """

        channel_id = channel.id  
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        
        webhook = await channel.create_webhook(name=server_name)
        if guild_document:

            channels = guild_document["channels"]  # Get the channels of the guild
            if any(ch["channel_id"] == channel_id for ch in channels):  # Check if the channel already exists
                return False  # Return False if the channel already exists

            channels.append({"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False})  # Add the new channel
            update_successful = await self.guild_repository.update({
                "server_id": guild_id,
                "channels": channels
            })
           
            if update_successful:
                for guild in self.guild_data:
                    if guild["server_id"] == guild_id:
                        guild["channels"] = channels
                        for channel in guild["channels"]:
                            if "activity" not in channel:
                                channel["activity"] = False



        else:
            insertion_successful = await self.guild_repository.create({
                "server_id": guild_id,
                "server_name": server_name,
                "channels": [{"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False}]
            })

            if insertion_successful:
                # Add the new guild to the cache only if the database insertion was successful
                self.guild_data.append({
                    "server_id": guild_id,
                    "server_name": server_name,
                    "channels": [{"channel_id": channel_id, "lobby_name": lobby_name, "webhook": webhook.url, "activity": False}],
                })

        return True

    async def update_guild_lobby(self, guild_id: int, channel_id: int, lobby_name: str):
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        if guild_document:
            channels = guild_document["channels"] 

            # Get's all the channel and change the lobby name then break
            for channel in channels:
                if channel["channel_id"] == channel_id:
                    channel["lobby_name"] = lobby_name
                    break
            update_successful = await self.guild_repository.update({
                "server_id": guild_id,
                "channels": channels
            })
           
            if update_successful:
                for guild in self.guild_data:
                    if guild["server_id"] == guild_id:
                        guild["channels"] = channels
                        for channel in guild["channels"]:
                            if "activity" not in channel:
                                channel["activity"] = False
     
    async def delete_guild_document(self, guild_id: int, channel_id: int):
       
        guild_document = None
        for guild in self.guild_data:  
            if guild["server_id"] == guild_id:  
                guild_document = guild
        # If data exists
        if guild_document:
            # Get all channels within the guild
            channels = guild_document["channels"]

            # Find the channel to delete and get its webhook
            channel_to_delete = next((channel for channel in channels if channel["channel_id"] == channel_id), None)
            
            if channel_to_delete:
                # Unregister the webhook
                discord_channel = self.bot.get_channel(channel_id)
                if discord_channel:
                    webhooks = await discord_channel.webhooks()
                    for webhook in webhooks:
                        if webhook.id == channel_to_delete["webhook"]:
                            await webhook.delete()
                            break

                # Remove the channel from the list
                channels = [channel for channel in channels if channel["channel_id"] != channel_id]

                # If there are still channels left, update the data
                if channels:
                    update_successful = await self.guild_repository.update({
                        "server_id": guild_id,
                        "channels": channels
                    })
                
                    if update_successful:
                        for guild in self.guild_data:
                            if guild["server_id"] == guild_id:
                                guild["channels"] = channels
                                for channel in guild["channels"]:
                                    if "activity" not in channel:
                                        channel["activity"] = False

                else:
                    # Otherwise, delete the guild document
                    result = await self.guild_repository.delete({"server_id": guild_id})
                    if result:
                        self.guild_data = [guild for guild in self.guild_data if guild["server_id"] != guild_id]
    
    async def create_moderator_role(self,role,level):
        
        role_data = None
        for data in self.moderator:
            if data["level"] == level:
                role_data = data

        if role_data:

            # Checks if the role exists
            mods  = role_data["mods"]
            if any(m["name"] == role["name"] for m in mods):
                return False

            # Add the user
            mods.append({
                "user_id": role["user_id"],
                "name": role["name"],
                "lobby_name" : role["lobby_name"]
            })
            update_successfull = await self.moderator_repository.update({
                    "level": level,
                    "mods" : mods
                 })
            
            if update_successfull:
                for mod in self.moderator:
                    if mod["level"] == level:
                        mod["mods"] = mods
                        return True
        else:
            insertion_successfull = await self.moderator_repository.create({
                "role_name" : role["role_name"],
                "icon": role["icon"],
                "level": role["level"],
                "mods" : []
            })

            if insertion_successfull:
                self.moderator.append({
                    "role_name" : role["role_name"],
                    "icon": role["icon"],
                    "level": role["level"],
                    "mods" : []
                })
                return True
   
    # This will only delete the mod data but not the role data
    async def delete_moderator_assigned_lobby(self, modData,role):
        
        mods = modData["mods"]
        # Filter out the lobby by lobby_name
        mods = [mod for mod in mods if mod["user_id"] != role["user_id"]]
        
        if mods:
            update_successful = await self.moderator_repository.update({
                "level": modData["level"],
                "mods" : mods
            })
            
            if update_successful:
                for data in self.moderator:
                    if data["level"] == modData["level"]:
                        data["mods"] = mods
                        return True
        else:
            return False
            # result = await self.moderator_repository.delete({"level": level})
            # if result:
            #     self.moderator = [mod for mod in self.moderator if mod["level"] !=level]
            #     return True

        

class MaliciousURLRepository():
    def __init__(self, db):
        self.collection = db.malurl_collection()

    async def findAll(self):
            cursor = self.collection.find()
            return await cursor.to_list(length=None)
        
    async def findOne(self,data):
        return await self.collection.find_one({"content" : data})
    
    async def create(self, data):
        if await self.findOne(data): 
            return None
        await self.collection.insert_one({
            "content" : data
        })
        return {
            "content" : data
        }
    
    async def delete(self,data):
        if await self.findOne(data): 
            return await self.collection.delete_one({
                "content" : data
            })
        else:
            return None

class MutedRepository():
    def __init__(self, db):
        self.collection = db.muted_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,id):
        return await self.collection.find_one({"id":id})
    
    async def create(self, data):
        return await self.collection.insert_one({
            "id": data["id"],
            "name":data["name"],
            "reason": data["reason"]
        })
    
    async def delete(self,id):
        return await self.collection.delete_one({
            "id": id,
        })       

class MaliciousWordsRepository():
    def __init__(self, db):
        self.collection = db.malword_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,data):
        return await self.collection.find_one({"content" : data})
    
    async def create(self, data):
        if await self.findOne(data): 
            return None
        await self.collection.insert_one({
            "content" : data
        })
        return {
            "content" : data
        }
    
    async def delete(self,data):
        return await self.collection.delete_one({
            "content" : data
        })
        
class LobbyRepository():
    def __init__(self,db):
        self.collection = db.lobby_collection()

    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self,lobbyname):
        return await self.collection.find_one({"lobbyname":lobbyname})
    
    async def create(self, data):
        if await self.findOne(data["lobbyname"]): 
            return None
        await self.collection.insert_one({
            "lobbyname": data["lobbyname"],
            "description": data["description"],
            "limit":data["limit"]
        })
        return {
            "lobbyname": data["lobbyname"],
            "description": data["description"],
            "limit":data["limit"]
        }
    
    async def delete(self,data):
        if await self.findOne(data["lobbyname"]): 
            return await self.collection.delete_one({
                "lobbyname": data["lobbyname"],
            })
        else:
            return None
        
    
    async def lobbylimit(self):
        response  = await self.findAll()
        if response:
            hashmap = {}
            for data in response:
                hashmap[data["lobbyname"]] = int(data["limit"])

            return hashmap
        

    async def getAllLobbies(self):
        response  = await self.findAll()
        if response:
            list = []
            for data in response:
                list.append(data)

            return list

class GuildRepository():
    def __init__(self, db):
        self.collection = db.guilds_collection()

    async def findFilter(self, filter):
        cursor = self.collection.find(filter)
        return await cursor.to_list(length=None)
    
    async def findAll(self):
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def findOne(self, server_id):
        return await self.collection.find_one({"server_id": server_id})

    async def create(self, data):
        if await self.findOne(data["server_id"]):  
            return None
        try:
            await self.collection.insert_one({
                "server_id": data["server_id"],
                "server_name": data["server_name"],
                "channels": data["channels"]
            }) 
            return True 
        except:
            return False

    async def delete(self,data):
        if await self.findOne(data["server_id"]):  
            await self.collection.delete_one({"server_id": data["server_id"]})  # Delete the guild document
            return True
        else:
            return False  
        
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