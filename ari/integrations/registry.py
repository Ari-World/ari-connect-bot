import logging
from dataclasses import dataclass
from typing import List

log = logging.getLogger("ari.integrations")


@dataclass(frozen=True)
class TrustedBotIntegration:
    """A bot-to-bot integration allowed to invoke Ari's commands.

    Discord ignores messages from other bot accounts by default; entries
    here are the deliberate, explicit exceptions. This pattern originated
    from a different contributor's FenderBot integration — kept and
    generalized so the next bot-to-bot integration is a one-file addition
    (a `build()` function reading its own env var, see `fenderbot.py`)
    plus one line in `load_integrations()` below, not a from-scratch
    rediscovery of `process_commands`.
    """
    name: str
    user_id: int


_trusted_bots: List[TrustedBotIntegration] = []


def load_integrations() -> List[TrustedBotIntegration]:
    """Builds every registered integration and caches the result.

    Must run after `core.config.load_config()` — each integration's
    `build()` reads its own env var, and those aren't populated in
    `os.environ` until `.env` has been loaded.
    """
    from . import fenderbot

    builders = [fenderbot.build]

    global _trusted_bots
    _trusted_bots = [
        integration
        for integration in (build() for build in builders)
        if integration is not None
    ]
    for integration in _trusted_bots:
        log.info("Registered trusted bot integration: %s (%s)", integration.name, integration.user_id)
    return _trusted_bots


def is_trusted_bot(user_id: int) -> bool:
    return any(integration.user_id == user_id for integration in _trusted_bots)
