import abc

import discord
from discord.ext import commands

class QuestionDB(abc.ABC):
    
    @abc.abstractmethod
    def add_condition(self, cond):
        pass

    @abc.abstractmethod
    def get_data_list(self):
        pass

class FirestoreQDB(QuestionDB):
    def __init__(self):
        pass

    def add_condition(self, cond):
        pass

    def get_data_list(self):
        return [
            {
                "url": "https://www.youtube.com/watch?v=yXxccEqgAO4",
                "name": "king",
                "singer": "Kano",
                "year": "2020"
            },
            {
                "url": "https://www.youtube.com/watch?v=XJLI4I2_ipE",
                "name": "World On Color",
                "singer": "Kano",
                "year": "2015"
            },
            {
                "url": "https://www.youtube.com/watch?v=FlqMQmS0cnU",
                "name": "Crossroad",
                "singer": "Yuiko",
                "year": "2012"
            }
        ]
        pass