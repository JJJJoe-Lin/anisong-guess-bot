import os, sys
from configparser import ConfigParser

from .sg import SongGuess
from .qdb import AnimeSgQDB
from .db import FirestoreDB
from .queue import QuestionQueue

def setup(bot):
    config = ConfigParser()
    
    if not config.read(os.path.join(os.path.dirname(__file__), "../config.ini")):
        print("Can't read config file", file=sys.stderr)
        return

    # initial database
    db_type = config.get("SongGuess", "database", fallback="firestore")
    if db_type == "firestore":
        key_path = config.get("Firestore", "key_path", fallback="./key.json")
        db = FirestoreDB(key_path)
    else:
        print("not support this type of database", file=sys.stderr)
        return

    # initial QDB
    qdb = AnimeSgQDB(bot, config, db)

    # initial question queue
    cache_size = config.getint("SongGuess", "downloaded_cache_size", fallback=5)
    thread_num = config.getint("SongGuess", "thread_num_for_downloading", fallback=4)
    q_queue = QuestionQueue(qdb, bot.loop, cache_size, thread_num)

    # initial song guess system
    sg = SongGuess(bot, config, q_queue)
    
    # add bot Cog
    bot.add_cog(qdb)
    bot.add_cog(sg)