import discord
from dotenv import load_dotenv
from discord.ext import commands
import logging
import os
from pathlib import Path
import importlib
import sys
from logging.handlers import RotatingFileHandler

import utils.botLoad as botLoad

load_dotenv()

log_directory = Path("logs")
log_directory.mkdir(exist_ok=True)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            log_directory / "bot.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("bot")

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.all()
        )

    print(botLoad.title)

    async def setup_hook(self):
        print(botLoad.loading_cogs)
        for file_path in Path('cogs').rglob('*.py'):
            if any(part.startswith('.') for part in file_path.parts):
                continue

            module_name = '.'.join(file_path.with_suffix('').parts)

            # Check if module has setup function
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                if not hasattr(module, 'setup'):
                    continue
            except Exception as e:
                logger.exception("Failed to import extension module=%s", module_name)
                print(botLoad.error(module_name, str(e)))
                continue

            try:
                await self.load_extension(module_name)
                print(botLoad.cog(module_name))
            except Exception as e:
                logger.exception("Failed to load extension module=%s", module_name)
                print(botLoad.error(module_name, str(e)))

        print(botLoad.loading_cogs_end)

        if os.getenv('GUILD_ID'):
            test_guild = discord.Object(id=int(os.getenv('GUILD_ID')))

            self.tree.copy_global_to(guild=test_guild)

            await self.tree.sync(guild=test_guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        logger.info("Bot connected user_id=%s", self.user.id if self.user else None)
        print(f'\n{self.user} is ready to work..')

bot = Bot()
bot.run(os.getenv('TOKEN'))
