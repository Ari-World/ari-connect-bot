"""The data layer — everything that reads or writes the seven MongoDB
collections behind global_chat.

    state.py         GlobalChatState — the in-memory cache, loaded once at
                      cog_load() and kept in sync by services after every
                      write. Also holds the pure query helpers
                      (find_guild-style lookups, permission checks,
                      malicious-content matching) that only need the cache,
                      not the database.
    repository.py     pure CRUD, one class per collection. The only file
                      that touches raw Mongo dicts — takes/returns typed
                      dataclasses from `domain/models.py` at every boundary.

Neither file makes Discord API calls. A service method that changes
something typically does: persist via `repository.py`, then mutate the
matching list on `state.py`, in that order.
"""
