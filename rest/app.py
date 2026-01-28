"""
Docstring for rest.app
"""

from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from db.customer_db import CustomerDB
from config.envconfig import EnvConfig


# ---------- Pydantic Models ----------
class Address(BaseModel):
    """
    Docstring for Address
    """

    street: str
    city: str
    state: str
    zip: str
    country: str


class Customer(BaseModel):
    """
    Docstring for Customer
    """

    customerid: str
    firstname: str
    lastname: str
    email: EmailStr
    phone: str
    address: Optional[Address] = None


class CustomerUpdate(BaseModel):
    """
    Docstring for CustomerUpdate
    """

    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[Address] = None


# ---------- App ----------
app = FastAPI(title="Customer API", version="1.0.0")

uri = EnvConfig().database_url
db_name = EnvConfig().db_name
collection_name = EnvConfig().collection_name
db = CustomerDB(uri=uri, db_name=db_name, collection_name=collection_name)


@app.get("/health")
def health():
    """
    Docstring for health
    """
    ok = db.health_check()
    if not ok:
        raise HTTPException(status_code=503, detail="MongoDB not healthy")
    return {"status": "ok", "mongo": "ok"}


@app.get("/customers", response_model=List[Customer])
def list_customers():
    """
    Docstring for list_customers
    """
    return db.list_customers()


@app.get("/customers/{customerid}", response_model=Customer)
def get_customer(customerid: str):
    """
    Docstring for get_customer

    :param customerid: Description
    :type customerid: str
    """
    customer = db.get_customer_by_id(customerid)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.post("/customers", status_code=201)
def create_customer(customer: Customer):
    """
    Docstring for create_customer

    :param customer: Description
    :type customer: Customer
    """
    # prevent duplicates (simple check)
    existing = db.get_customer_by_id(customer.customerid)
    if existing:
        raise HTTPException(status_code=409, detail="customerid already exists")

    db.create_customer(customer.model_dump())
    return {"message": "created", "customerid": customer.customerid}


@app.put("/customers/{customerid}")
def update_customer(customerid: str, updates: CustomerUpdate):
    """
    Docstring for update_customer

    :param customerid: Description
    :type customerid: str
    :param updates: Description
    :type updates: CustomerUpdate
    """
    patch: Dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    ok = db.update_customer(customerid, patch)
    if not ok:
        raise HTTPException(
            status_code=404, detail="Customer not found (or no changes)"
        )
    return {"message": "updated", "customerid": customerid}


@app.delete("/customers/{customerid}")
def delete_customer(customerid: str):
    """
    Docstring for delete_customer

    :param customerid: Description
    :type customerid: str
    """
    ok = db.delete_customer(customerid)
    if not ok:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "deleted", "customerid": customerid}
