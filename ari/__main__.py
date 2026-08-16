"""Entry point — run with `cd ari && python __main__.py` (not `python -m ari`
from the repo root; see CLAUDE.md for why). Startup/shutdown orchestration
lives in `core/runner.py`; this file just invokes it, since that's what a
top-level `__main__.py` needs to be for the run command above to work.

#
#                   Ari - Connect
#                  ( Early Access )
#
#   Original Idea by Flames / Aryan
#   Further Developed by Khesir
#
"""
from core.runner import main

if __name__ == "__main__":
    main()
