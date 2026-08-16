"""External bot-to-bot integrations. Discord ignores messages from other
bot accounts by default; entries here are the deliberate, explicit
exceptions to that rule, checked by `core/bot.py`'s `process_commands`
override.

    registry.py     TrustedBotIntegration dataclass + load_integrations()
    fenderbot.py    FenderBot's own integration — the template for the next one

To add a new integration: write a `build()` function in a new file here
(see `fenderbot.py`) that reads its own env var and returns a
`TrustedBotIntegration` or `None`, then add it to the `builders` list in
`registry.load_integrations()`. No changes to `core/bot.py` needed.
Registration happens lazily in `Ari._pre_login()` — never at import time,
since `.env` isn't loaded yet when this package is first imported.
"""
