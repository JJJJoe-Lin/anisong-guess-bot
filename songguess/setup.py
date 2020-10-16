import os, sys
from configparser import ConfigParser

from . import SongGuess

def setup(bot):
    config = ConfigParser()
    
    if not config.read(os.path.join(os.path.dirname(__file__), "../config.ini")):
        print("Can't read config file", file=sys.stderr)
        return

    sg = SongGuess(bot, config)
    bot.add_cog(sg)