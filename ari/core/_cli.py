


# This needs to be an int enum to be used
# with sys.exit
from enum import IntEnum


class ExitCodes(IntEnum):
    #: Clean shutdown (through signals, keyboard interrupt, [p]shutdown, etc.).
    SHUTDOWN = 0
    #: An unrecoverable error occurred during application's runtime.
    CRITICAL = 1
    #: The CLI command was used incorrectly, such as when the wrong number of arguments are given.
    INVALID_CLI_USAGE = 2
    #: Restart was requested by the bot owner (probably through [p]restart command).
    RESTART = 26
    #: Some kind of configuration error occurred.
    CONFIGURATION_ERROR = 78  # Exit code borrowed from os.EX_CONFIG.


