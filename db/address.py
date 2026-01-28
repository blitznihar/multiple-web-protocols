"""Database models for address information."""

from pydantic import BaseModel


class Address(BaseModel):
    """
    Docstring for Address
    """

    street: str
    city: str
    state: str
    zip: str
    country: str
