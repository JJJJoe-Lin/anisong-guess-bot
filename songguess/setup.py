import os, sys
from configparser import ConfigParser

from .sg import SongGuess
from .sql import FirestoreSGSQL
from .scoring import Scoring

def setup(bot):
    config = ConfigParser()
    
    if not config.read(os.path.join(os.path.dirname(__file__), "../config.ini")):
        print("Can't read config file", file=sys.stderr)
        return

    scoring = Scoring()
    sql = FirestoreSGSQL()
    sg = SongGuess(bot, config, scoring, sql)

    bot.add_cog(scoring)
    bot.add_cog(sql)
    bot.add_cog(sg)