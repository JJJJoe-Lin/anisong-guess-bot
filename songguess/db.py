import abc
from typing import Union, List

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore import Query

class DatabaseABC(abc.ABC):

    @abc.abstractmethod
    def exec_query(self, query, ref):
        pass

    @abc.abstractmethod
    def get_results(self, ref):
        pass

class FirestoreDB(DatabaseABC):
    def __init__(self, key_path: str, collection: str):
        cred = firebase_admin.credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)         # ValueError

        self.db = firebase_admin.firestore.client()     # type: firestore.Client
        self.ref = self.db.collection(collection)

    def prepare(self):
        pass

    def exec_query(self, query: list, ref: Union[None, Query]) -> Query:
        if len(query) != 3:
            raise ValueError
        if ref is None:
            ref = self.ref
        elif not isinstance(ref, Query):
            raise ValueError
        return ref.where(*query)

    def get_results(self, ref: Union[None, Query]) -> List[dict]:
        # return [
        #     {
        #         "url": "https://www.youtube.com/watch?v=yXxccEqgAO4",
        #         "name": "king",
        #         "singer": "Kano",
        #         "year": "2020"
        #     },
        #     {
        #         "url": "https://www.youtube.com/watch?v=XJLI4I2_ipE",
        #         "name": "World On Color",
        #         "singer": "Kano",
        #         "year": "2015"
        #     },
        #     {
        #         "url": "https://www.youtube.com/watch?v=FlqMQmS0cnU",
        #         "name": "Crossroad",
        #         "singer": "Yuiko",
        #         "year": "2012"
        #     }
        # ]
        if ref is None:
            ref = self.ref
        elif not isinstance(ref, Query):
            raise ValueError
        return [doc.to_dict() for doc in ref.stream()]