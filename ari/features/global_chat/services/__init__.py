"""global_chat's business logic — the layer between the thin cogs in
`cogs/` and the pure data layers (`persistence/state.py`,
`persistence/repository.py`).

    lobby_service.py               lobby lookup/validation/creation
    guild_connection_service.py    connect/unlink/switch + webhook lifecycle + join announcements
    relay_service.py               the webhook-relay engine (send/edit/delete across a lobby)
    moderation_service.py          permission levels, mute list, banned word/link lists, roles
    audit_log_service.py           Discord-side audit logging (log_mod, log_report, etc.)
    cache_manager.py               per-lobby message cache, for edit/delete linking — lives here
                                    because relay_service.py is its main consumer, not because it
                                    orchestrates repo+state+Discord the way the others do (it
                                    doesn't touch the repository or state at all)

A service method that changes something typically does: persist via the
repository, then mutate the matching list on `state`, in that order — no
Discord `ctx`/`interaction` objects should reach this deep; cogs pass in
plain values (ids, strings, already-fetched Discord objects), not the
command context itself.
"""
