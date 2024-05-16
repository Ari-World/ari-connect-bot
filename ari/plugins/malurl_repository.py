

class MaliciousURLRepository():
    def __init__(self, db):
        self.db = db
        self.collection = self.db.malurl_collection

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