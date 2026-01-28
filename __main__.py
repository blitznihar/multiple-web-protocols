"""
Docstring for __main__
"""

from db.customer_db import CustomerDB
from config.envconfig import EnvConfig


def main():
    """
    Docstring for main
    """
    print("Hello from multiple-web-protocols!")
    config = EnvConfig()
    uri = config.database_url
    db_name = config.db_name
    collection_name = config.collection_name

    db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)

    # Create
    db.create_customer(
        {
            "customerid": "99993",
            "firstname": "Nihar",
            "lastname": "Malali",
            "email": "nihar99993@example.com",
            "phone": "+1-555-1111",
        }
    )

    # Read one
    print(db.get_customer_by_id("99993"))
    # List all
    print(db.list_customers())

    # Update
    db.update_customer("99993", {"phone": "+1-555-2222"})

    # Delete
    db.delete_customer("99993")

    db.close()


if __name__ == "__main__":
    main()
