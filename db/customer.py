"""
Docstring for db.customer
"""

from pydantic import BaseModel
from db.address import Address


class Customer(BaseModel):
    """
    Docstring for Customer
    """

    customerid: str
    firstname: str
    lastname: str
    email: str
    phone: str
    address: Address | None = None
