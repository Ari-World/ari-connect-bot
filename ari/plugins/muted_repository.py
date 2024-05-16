

class MutedRepository():
    def __init__(self, db):
        self.db = db
        self.collection = self.db.muted_collection

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
        