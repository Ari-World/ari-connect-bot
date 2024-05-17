
import sys as _sys

# TODO: Planning to put this inside __init__.py but it doesnt work smh
def _ensure_no_colorama():
    # a hacky way to ensure that nothing initialises colorama
    # if we're not running with legacy Windows command line mode
    # from rich.console import detect_legacy_windows

    # if not detect_legacy_windows():
    #     try:
    #         import colorama
    #         import colorama.initialise
    #     except ModuleNotFoundError:
    #         # colorama is not ari's primary dependency so it might not be present
    #         return

    #     colorama.deinit()

    #     def _colorama_wrap_stream(stream, *args, **kwargs):
    #         return stream

    #     colorama.wrap_stream = _colorama_wrap_stream
    #     colorama.initialise.wrap_stream = _colorama_wrap_stream
    pass
def _update_event_loop_policy():
    if _sys.implementation.name == "cpython":
        # Let's not force this dependency, uvloop is much faster on cpython
        try:
            import uvloop
        except ImportError:
            print()
            pass
        else:
            import asyncio

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def _early_init():
    # This function replaces logger so we preferably (though not necessarily) want that to happen
    # before importing anything that calls `logging.getLogger()`, i.e. `asyncio`.
    _update_event_loop_policy()
    #_ensure_no_colorama()

