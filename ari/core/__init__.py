"""The bot chassis — infrastructure, not features.

    bot.py           the Ari commands.Bot subclass: startup/shutdown, the
                      explicit FEATURES cog registry, the trusted-bot
                      process_commands override
    runner.py        process-level orchestration — the event loop, exception
                      handlers, and graceful shutdown behind `python __main__.py`
    config.py        typed AppConfig — load_config() once, get_config() everywhere
    custom_logging.py  Rich-based console logging setup
    presenters.py    pure embed-builders for core-level messages (e.g. the
                      new-guild welcome embed)
    _events.py       Discord lifecycle event registration
    _cli.py          process exit codes
    _driver/         the MongoDB connection (StaticDatabase)
    utils/           shared helper modules (chat_formatting, utility)
    commands/        generic, non-feature-specific cogs (Utils, Info)

Nothing here should import from `features/` — features depend on core,
never the other way around.
"""
