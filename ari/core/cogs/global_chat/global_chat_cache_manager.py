

import asyncio

import logging


log = logging.getLogger("globalchat.cache_manager")


class CacheManager:
    def __init__(self):
        self.cacheMessages = []
        self.deleteMessageThreshold = 3600

        log.info("Caching Manager Ready")

    def createCache(self,lobbies):
        for lobby in lobbies:
            data =  {
                "lobbyname": lobby["lobbyname"],
                "messages": []
            }
            self.cacheMessages.append(data)

    def delete_cache_message(self, source_id,lobbyName):
        for message in self.cacheMessages:
            if message["lobbyname"] == lobbyName:
                for source in message["messages"]:
                    if source["source"] == source_id:
                        message["messages"].remove(source)
                        return 
                    
    async def schedule_delete_cache_message(self, source_id, lobby_name):
        
        await asyncio.sleep(self.deleteMessageThreshold)
        self.delete_cache_message(source_id, lobby_name)

    async def cache_message(self, lobby_name, messagesData):
        for data in self.cacheMessages:
            if data["lobbyname"] == lobby_name:
                data["messages"].append(messagesData)
                await self.schedule_delete_cache_message(messagesData["source"], lobby_name)
    
    def find_source_data(self, message_id, lobby_name):
        for data in self.cacheMessages:
            if data["lobbyname"] == lobby_name:
                for messages in data["messages"]:
                    if messages["source"] == message_id:
                        return messages
                    for webhook in messages["webhooksent"]:
                        if webhook["messageId"] == message_id:
                            return messages
        return None
    
    def findCachedLobby(self, lobbyName):
        """
            Finds the cache message 

            Args:
                lobbyname (str) : The name of the specified lobby
            
            Returns:
                dict : the cache memory if found, otherwise none
        """

        for data in self.cacheMessages:
            if lobbyName == data["lobbyname"]:
                return data
        
        return None