import asyncio
import functools
import sys

from core.bot import Ari

def shutdown_handler(ari: Ari):
    sys.exit("I now die")

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
        print("The main bot task didn't handle an exception and has crashed ")
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
        print("0h got Ctrl + C to Shutdown Ari! (attempting to kms)")
        print("Received KeybpardIOnterrupt, treating as interrupt")
        if ari is not None:
            loop.run_until_complete(shutdown_handler(ari))
    except SystemExit as exc:
        # Also catch this one as stated, any exception which normally
        # kills the python interprter (Base Exceptions Mminus asyncio.cancelled)
        # Need to do something with prior having the loop close
        if ari is not None:
            loop.run_until_complete(shutdown_handler(ari))
    finally:
        # Allows transports to close properly, and prevent new one from being opened.
        
        # This is to properly clsoe any asyncronouse tasks
        # Still yet to understand and read the documentation.
        loop.run_until_complete(loop.shutdown_asyncgens())

        print("Please wait, cleaning up a bit more")
        loop.run_until_complete(asyncio.sleep(2))
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()
    # Something fancy! 


if __name__ == "__main__":
    main()
