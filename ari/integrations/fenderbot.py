import os
from typing import Optional

from .registry import TrustedBotIntegration


def build() -> Optional[TrustedBotIntegration]:
    """FenderBot integration — lets FenderBot's messages invoke Ari's
    commands despite the normal ignore-other-bots rule.

    Configure via the FENDERBOT_USER_ID env var; leave it unset to disable
    this integration entirely.
    """
    user_id = os.getenv("FENDERBOT_USER_ID")
    if not user_id:
        return None
    return TrustedBotIntegration(name="FenderBot", user_id=int(user_id))
