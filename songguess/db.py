import abc
from typing import Union, List

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore import Query

class DatabaseABC(abc.ABC):

    @abc.abstractmethod
    def exec_get(self, ref, query):
        pass

class FirestoreDB(DatabaseABC):
    def __init__(self, key_path: str):
        cred = firebase_admin.credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)         # ValueError

        self.db = firebase_admin.firestore.client()     # type: firestore.Client

    def exec_get(self, collection: str, query: list):
        db_query = ref = self.db.collection(collection)
        for q in query:
            db_query = ref.where(*q)
        return db_query.get()

    def exec_add(self, collection: str, data: dict):
        if not isinstance(data, dict):
            raise ValueError
        ref = self.db.collection(collection).document()
        ref.set(data)

    def exec_clear(self, collection: str):
        ref = self.db.collection(collection)
        docs = ref.stream()
        for doc in docs:
            doc.reference.delete()

    # def exec_query(self, query: list, ref: Union[None, Query]) -> Query:
    #     if len(query) != 3:
    #         raise ValueError
    #     if ref is None:
    #         ref = self.ref
    #     elif not isinstance(ref, Query):
    #         raise ValueError
    #     return ref.where(*query)

    # def get_results(self, ref: Union[None, Query]) -> List[dict]:
    #     if ref is None:
    #         ref = self.ref
    #     elif not isinstance(ref, Query):
    #         raise ValueError
    #     return [doc.to_dict() for doc in ref.stream()]