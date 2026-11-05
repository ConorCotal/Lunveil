import asyncio
import inspect
import pkgutil
import importlib
from pathlib import Path

from ..UI import Buttons, Embeds, Modals


class Handlers:
    def __init__(self, bot):
        self.bot = bot
        self.pending_ticket_creations = {}

        # create embeds early so sub-handlers can reference it in their __init__
        self.embeds = Embeds(bot)

        # dynamically discover and instantiate sub-handlers placed in this package
        handlers_pkg = __name__
        pkg_path = Path(__file__).parent

        for _finder, module_name, _ispkg in pkgutil.iter_modules([str(pkg_path)]):
            if module_name.startswith("__"):
                continue
            module = importlib.import_module(f"{handlers_pkg}.{module_name}")
            for cls_name, cls_obj in inspect.getmembers(module, inspect.isclass):
                if cls_obj.__module__ != module.__name__:
                    continue
                if not cls_name.endswith("Handler"):
                    continue

                base = cls_name[:-7]
                attr_name = f"{base.lower()}_handler"
                if hasattr(self, attr_name):
                    continue

                instance = cls_obj(bot, self)
                setattr(self, attr_name, instance)

                # register public methods from this handler onto the facade
                self._register_handler_methods(instance)

        # now create modals and buttons which may reference facade methods
        self.modals = Modals(bot, self)
        self.buttons = Buttons(bot, self)

    def _register_handler_methods(self, handler):
        for name, member in inspect.getmembers(handler, predicate=inspect.ismethod):
            if name.startswith("_") or name == "__init__":
                continue
            if hasattr(self, name):
                continue
            setattr(self, name, member)
