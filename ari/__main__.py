
import asyncio
from enum import IntEnum
import functools
import logging
import sys
from core.bot import Ari

log = logging.getLogger("ari.main")

# This needs to be an int enum to be used
# with sys.exit
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



def shutdown_handler(ari: Ari,signal_type=None, exit_code=None):
    if signal_type:
        log.info("%s received. Quitting...", signal_type.name)
        # Do not collapse the below line into other logic
        # We need to renter this function
        # after it interrupts the event loop.
        sys.exit(ExitCodes.SHUTDOWN)
    elif exit_code is None:
        log.info("Shutting down from unhandled exception")
        ari._shutdown_mode = ExitCodes.CRITICAL

    # TODO: Handles Ari Shutdown
    # if exit_code is not None:
    #     ari._shutdown_mode = exit_code

    # try:
    #     if not ari.is_closed():
    #         await ari.close()
    # finally:
    #     # Then cancels all outstanding tasks other than ourselves
    #     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    #     [task.cancel() for task in pending]
    #     await asyncio.gather(*pending, return_exceptions=True)

def ari_exception_handler(ari, task: asyncio.Future):
    """
    This is set as a done callback for Ari

    must be used with functools.partial

    If the main bot.run dies for some reason,
    we don't want to swallow the exception and hang.
    """
    try:
        task.result()
    except (SystemExit, KeyboardInterrupt, asyncio.CancelledError):
        pass # Handled by the global_exception_handler, or cancellation
    except Exception as exc:
        log.critical("The main bot task didn't handle an exception and has crashed", exc_info=exc)
        log.warning("Attempting to die as gracefully as possible...")
        asyncio.create_task(shutdown_handler(ari))

def global_exception_handler(red, loop, context):
    """
    Logs unhandled exceptions in other tasks
    """
    exc = context.get("exception")
    # These will get handled later when it *also* kills loop.run_forever
    if exc is not None and isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return
    loop.default_exception_handler(context)

async def run_bot(ari : Ari) -> None:
    """
    This runs the bot.
    """
    ari.logging.init_logging(
        level = 0
    )
    # TODO: Maybe setting the bot configuration or manipulating the config here is a good practice.
    await ari.start()
    return None

def main():
    ari = None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        ari = Ari()

        exc_handler = functools.partial(global_exception_handler,ari)
        loop.set_exception_handler(exc_handler)
        fut = loop.create_task(run_bot(ari))
        a_ex_handler = functools.partial(ari_exception_handler,ari)
        fut.add_done_callback(a_ex_handler)
        loop.run_forever()
    except KeyboardInterrupt:
        log.warning("Please do not use Ctrl+C to Shutdown Ari! (attempting to die gracefully...)")
        log.error("Received KeyboardInterrupt, treating as interrupt")
        if ari is not None:
            loop.run_until_complete(shutdown_handler(ari))
    except SystemExit as exc:
        # Also catch this one as stated, any exception which normally
        # kills the python interprter (Base Exceptions Mminus asyncio.cancelled)
        # Need to do something with prior having the loop close
        exit_code = int(exc.code)
        try:
            exit_code_name = ExitCodes(exit_code).name
        except ValueError:
            exit_code_name = "UNKNOWN"
        log.info("Shutting down with exit code: %s (%s)", exit_code, exit_code_name)
        if ari is not None:
            loop.run_until_complete(shutdown_handler(ari, None, exc.code))
    except Exception as exc: # Non Standard case.
        log.exception("Unexpected exception (%s): ", type(exc), exc_info=exc)
        if ari is not None:
            loop.run_until_complete(shutdown_handler(ari, None, ExitCodes.CRITICAL))
    finally:
        # Allows transports to close properly, and prevent new one from being opened.
        
        # This is to properly clsoe any asyncronouse tasks
        # Still yet to understand and read the documentation.
        loop.run_until_complete(loop.shutdown_asyncgens())

        log.info("Please wait, cleaning up a bit more")
        loop.run_until_complete(asyncio.sleep(2))
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()
    # Something fancy! 
    sys.exit()


if __name__ == "__main__":
    main()
