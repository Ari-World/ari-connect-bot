from importlib import import_module
from importlib.machinery import ModuleSpec
from typing import List, Optional
import pkgutil
import importlib
import cogs
import logging

log = logging.getLogger("cog_manager")

class NoSuchCog(ImportError):
    """Thrown when a cog is missing.

    Different from ImportError because some ImportErrors can happen inside cogs.
    """


class CogManager:
    """Directory manager for Red's cogs.

    This module allows you to load cogs from multiple directories and even from
    outside the bot directory. You may also set a directory for downloader to
    install new cogs to, the default being the :code:`cogs/` folder in the root
    bot directory.
    """

    
    async def find_cogs(self) -> List[ModuleSpec]:
        """
        Attempts to find specs for all core cogs in the package and sub-packages.

        Returns
        -------
        List[importlib.machinery.ModuleSpec]
            A list of module specifications for the cogs.

        Raises
        ------
        RuntimeError
            When no matching spec can be found.
        """

        package = cogs
        cogs_specs = []

        for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if not ispkg:  # Skip packages, only import modules
                try:
                    mod = importlib.import_module(modname)
                    cogs_specs.append(mod.__spec__)
                except ImportError as e:
                    log.error(f"Failed to import cog module '{modname}': {e}")

        if not cogs_specs:
            log.error("No core cogs could be found in the package.")

        return cogs_specs