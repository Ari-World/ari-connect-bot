"""The MongoDB connection. Just `_mongo.py`'s `StaticDatabase` — a
classmethod-only singleton that lazily connects on first use and exposes
one accessor per collection. Nothing else should reach for
`AsyncIOMotorClient` directly; go through `StaticDatabase`.
"""
