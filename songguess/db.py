import abc

class QuestionDB(abc.ABC):
    
    @abc.abstractmethod
    def prepare(self):
        pass

    @abc.abstractmethod
    def exec_query(self, query):
        pass

    @abc.abstractmethod
    def get_result(self):
        pass

class FirestoreQDB(QuestionDB):
    def __init__(self):
        pass

    def prepare(self):
        pass

    def exec_query(self, query):
        pass

    def get_result(self):
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