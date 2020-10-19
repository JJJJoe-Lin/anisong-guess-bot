import os, sys
from configparser import ConfigParser

from .sg import SongGuess
from .qdb import SgQDB
from .scoring import Scoring
from .db import FirestoreDB

def setup(bot):
    config = ConfigParser()
    
    if not config.read(os.path.join(os.path.dirname(__file__), "../config.ini")):
        print("Can't read config file", file=sys.stderr)
        return

    # initial database
    db_type = config.get("Bot", "database", fallback="firestore")
    if db_type == "firestore":
        db = FirestoreDB(config.get("Firestore", "key_path", fallback="./key.json"),
                         config.get("Firestore", "collection", fallback="anime_song"))
    else:
        print("not support this type of database", file=sys.stderr)
        return

    scoring = Scoring(bot, config)
    qdb = SgQDB(bot, config, db)
    sg = SongGuess(bot, config, scoring, qdb)

    bot.add_cog(scoring)
    bot.add_cog(qdb)
    bot.add_cog(sg)