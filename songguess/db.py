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
        
        pass