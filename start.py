import os, sys
from configparser import ConfigParser

from discord.ext.commands import Bot

config = ConfigParser()

if not config.read(os.path.join(os.path.dirname(__file__), "config.ini")):
    print("Can't read config file", file=sys.stderr)
    sys.exit(-1)

command_prefix = config.get("Bot", "command_prefix", fallback="#")
token = config.get("Bot", "token", fallback="")

bot = Bot(command_prefix=command_prefix)
bot.load_extension(f'songguess.setup')

@bot.event
async def on_ready():
    print("Bot is online")

if __name__ == "__main__":
    bot.run(token)
