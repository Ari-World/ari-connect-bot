


class AriError(Exception):
    """Base error class for Ari-related errors."""

class MissingExtraRequirements(AriError):
    """Raised when an extra requirement is missing but required."""
