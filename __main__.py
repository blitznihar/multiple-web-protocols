"""
Docstring for __main__
"""
from db.customer_db import CustomerDB


def main():
    """
    Docstring for main
    """
    print("Hello from multiple-web-protocols!")
    db = CustomerDB()

    # Create
    db.create_customer(
        {
            "customerid": "99999",
            "firstname": "Nihar",
            "lastname": "Malali",
            "email": "nihar@example.com",
            "phone": "+1-555-1111",
        }
    )

    # Read one
    print(db.get_customer_by_id("99999"))

    # List all
    print(db.list_customers())

    # Update
    db.update_customer("99999", {"phone": "+1-555-2222"})

    # Delete
    db.delete_customer("99999")

    db.close()


if __name__ == "__main__":
    main()
