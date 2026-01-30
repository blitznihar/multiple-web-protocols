from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip: str
    country: str


class Customer(BaseModel):
    customerid: str = Field(..., description="Primary key")
    firstname: str
    lastname: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[Address] = None
