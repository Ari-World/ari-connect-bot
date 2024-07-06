

import asyncio

import logging

from ...data_mananger import getCacheThreshold

log = logging.getLogger("globalchat.cache_manager")


class CacheManager:
    def __init__(self):
        self.cacheMessages = []
        self.deleteMessageThreshold = int(getCacheThreshold())

        log.info("Caching Manager Ready")

    def createCache(self,lobbies):
        for lobby in lobbies:
            data =  {
                "lobby_id": lobby["lobby_id"],
                "messages": []
            }
            self.cacheMessages.append(data)

    def delete_cache_message(self, source_id,lobby_id):
        for message in self.cacheMessages:
            if message["lobby_id"] == lobby_id:
                for source in message["messages"]:
                    if source["source"] == source_id:
                        message["messages"].remove(source)
                        return 
                    
    async def schedule_delete_cache_message(self, source_id, lobby_id):
        
        await asyncio.sleep(self.deleteMessageThreshold)
        self.delete_cache_message(source_id, lobby_id)

    async def cache_message(self, lobby_id, messagesData):
        for data in self.cacheMessages:
            if data["lobby_id"] == lobby_id:
                data["messages"].append(messagesData)
                await self.schedule_delete_cache_message(messagesData["source"], lobby_id)
    
    def find_source_data(self, message_id, lobby_id):
        for data in self.cacheMessages:
            if data["lobby_id"] == lobby_id:
                for messages in data["messages"]:
                    if messages["source"] == message_id:
                        return messages
                    for webhook in messages["webhooksent"]:
                        if webhook["messageId"] == message_id:
                            return messages
        return None
    
    def findCachedLobby(self, lobby_id):
        """
            Finds the cache message 

            Args:
                lobby_id (str) : The name of the specified lobby
            
            Returns:
                dict : the cache memory if found, otherwise none
        """

        for data in self.cacheMessages:
            if lobby_id == data["lobby_id"]:
                return data
        
        return None