

import asyncio

import logging

from core.config import get_config

log = logging.getLogger("globalchat.cache_manager")


class CacheManager:
    def __init__(self):
        self.cacheMessages = []
        self.deleteMessageThreshold = int(get_config().cache_threshold)

        log.info("Caching Manager Ready")

    async def createCache(self,lobby):
        data =  {
            "lobby_id": lobby[0]['lobby_id'],
            "messages": []
        }
        self.cacheMessages.append(data)
        await self.cache_message( lobby[0]['lobby_id'], lobby)

    def delete_cache_message(self, messageData):
        for message in self.cacheMessages:
            if message["lobby_id"] == messageData[0]['lobby_id']:
                for source in message["messages"]:
                    if source[0]["message_id"] == messageData[0]['message_id']:
                        message["messages"].remove(source)
                        return 
                    
    async def schedule_delete_cache_message(self, messageData):
        
        await asyncio.sleep(self.deleteMessageThreshold)

        self.delete_cache_message(messageData)

    async def cache_message(self, lobby_id, messagesData):
        for message in self.cacheMessages:
            if message["lobby_id"] == lobby_id:
                message["messages"].append(messagesData)
                await self.schedule_delete_cache_message(messagesData)
                return
        
        await self.createCache(messagesData)
        
    def find_source_by_message_id(self,message_id, lobby_id):
        for data in self.cacheMessages:
            if data["lobby_id"] == lobby_id:
               for source in data['messages']:
                   for msg in source:
                       if msg['message_id'] == message_id:
                           return source