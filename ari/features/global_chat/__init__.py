"""Global Chat — the bot's core feature: cross-server chat relayed across
every channel connected to the same lobby, via per-channel webhooks.

    global_chat.py    GlobalChatManager — wiring only, constructs every
                       service/repo/state and registers this feature's cogs
    domain/               the domain layer — one dataclass per persisted shape
    persistence/          in-memory cache (state.py) + pure CRUD (repository.py)
    services/             business logic (lobby, connection, relay, moderation,
                           audit log, and the per-lobby message cache)
    cogs/                 the actual Discord commands and event listeners
    ui/                   presentation — views.py (modals/dropdowns/pagination)
                           and presenters.py (pure embed-builders)

Layering rule: cogs are thin (parse input -> call a service -> render via
a presenter -> send). Business logic lives in services/, not in a cog.
See /CLAUDE.md at the repo root for the full write-up, including the
documented deviations from this shape (on_join_announce's home, the
global-vs-per-lobby moderation decision, /settings' lack of persistence).
"""
