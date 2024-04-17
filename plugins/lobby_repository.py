

class LobbyRepository():
    def __init__(self, db):
        self.db = db
        self.collection = self.db.lobby_collection

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
        