from ..UI import Buttons, Embed, Modals
from .create import CreateHandler
from .edit import EditHandler
from .manage import ManageHandler


class Handlers:
    def __init__(self, bot, repository):
        self.bot = bot
        self.repository = repository
        self.pending_kp_creations = {}
        self.embed = Embed(bot)
        self.create = CreateHandler(bot, self)
        self.edit = EditHandler(bot, self)
        self.manage = ManageHandler(bot, self)
        self.modals = Modals(bot, self)
        self.buttons = Buttons(bot, self)
