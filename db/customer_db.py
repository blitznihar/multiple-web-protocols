"""
Docstring for db.customer_db
"""

from typing import List, Dict, Optional
from pymongo import MongoClient


class CustomerDB:
    """
    Docstring for CustomerDB
    """

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "customerdb",
        collection_name: str = "customers",
    ):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    # -------------------------
    # CREATE
    # -------------------------
    def create_customer(self, customer: Dict) -> str:
        result = self.collection.insert_one(customer)
        return str(result.inserted_id)

    # -------------------------
    # READ (ONE)
    # -------------------------
    def get_customer_by_id(self, customerid: str) -> Optional[Dict]:
        return self.collection.find_one({"customerid": customerid}, {"_id": 0})

    # -------------------------
    # READ (ALL)
    # -------------------------
    def list_customers(self) -> List[Dict]:
        return list(self.collection.find({}, {"_id": 0}))

    # -------------------------
    # UPDATE
    # -------------------------
    def update_customer(self, customerid: str, updates: Dict) -> bool:
        result = self.collection.update_one(
            {"customerid": customerid}, {"$set": updates}
        )
        return result.modified_count > 0

    # -------------------------
    # DELETE
    # -------------------------
    def delete_customer(self, customerid: str) -> bool:
        result = self.collection.delete_one({"customerid": customerid})
        return result.deleted_count > 0

    # -------------------------
    # CLOSE CONNECTION
    # -------------------------
    def close(self):
        self.client.close()
