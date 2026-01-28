"""
Docstring for grpc.server
"""

from concurrent import futures
import grpc
from pymongo.errors import DuplicateKeyError
from config.envconfig import EnvConfig
from db.customer_db import CustomerDB
from .customerpb import customer_pb2, customer_pb2_grpc  # type: ignore


def customer_msg_to_dict(c: customer_pb2.Customer) -> dict:
    """
    Docstring for customer_msg_to_dict

    :param c: Description
    :type c: customer_pb2.Customer
    :return: Description
    :rtype: dict
    """
    doc = {
        "customerid": c.customerid,
        "firstname": c.firstname,
        "lastname": c.lastname,
        "email": c.email,
        "phone": c.phone,
    }

    addr = {
        "street": c.address.street,
        "city": c.address.city,
        "state": c.address.state,
        "zip": c.address.zip,
        "country": c.address.country,
    }
    if any(v.strip() for v in addr.values()):
        doc["address"] = addr

    return doc


def dict_to_customer_msg(doc: dict) -> customer_pb2.Customer:
    addr = doc.get("address") or {}
    return customer_pb2.Customer(
        customerid=doc.get("customerid", ""),
        firstname=doc.get("firstname", ""),
        lastname=doc.get("lastname", ""),
        email=doc.get("email", ""),
        phone=doc.get("phone", ""),
        address=customer_pb2.Address(
            street=addr.get("street", ""),
            city=addr.get("city", ""),
            state=addr.get("state", ""),
            zip=addr.get("zip", ""),
            country=addr.get("country", ""),
        ),
    )


def build_update_dict(customer: customer_pb2.Customer) -> dict:
    updates = {}
    if customer.firstname:
        updates["firstname"] = customer.firstname
    if customer.lastname:
        updates["lastname"] = customer.lastname
    if customer.email:
        updates["email"] = customer.email
    if customer.phone:
        updates["phone"] = customer.phone

    addr_updates = {}
    if customer.address.street:
        addr_updates["street"] = customer.address.street
    if customer.address.city:
        addr_updates["city"] = customer.address.city
    if customer.address.state:
        addr_updates["state"] = customer.address.state
    if customer.address.zip:
        addr_updates["zip"] = customer.address.zip
    if customer.address.country:
        addr_updates["country"] = customer.address.country

    for k, v in addr_updates.items():
        updates[f"address.{k}"] = v

    return updates


class CustomerService(customer_pb2_grpc.CustomerServiceServicer):
    def __init__(self):
        mongo_uri = EnvConfig().database_url
        db_name = EnvConfig().db_name
        collection_name = EnvConfig().collection_name
        self.db = CustomerDB(
            uri=mongo_uri, db_name=db_name, collection_name=collection_name
        )

    def CreateCustomer(self, request, context):
        if not request.customer.customerid:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("customerid is required")
            return customer_pb2.CreateCustomerResponse(
                ok=False, message="customerid is required"
            )

        try:
            self.db.create_customer(customer_msg_to_dict(request.customer))
            return customer_pb2.CreateCustomerResponse(ok=True, message="created")
        except DuplicateKeyError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("customerid already exists")
            return customer_pb2.CreateCustomerResponse(
                ok=False, message="already exists"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return customer_pb2.CreateCustomerResponse(
                ok=False, message="internal error"
            )

    def GetCustomerById(self, request, context):
        doc = self.db.get_customer_by_id(request.customerid)
        if not doc:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("customer not found")
            return customer_pb2.GetCustomerByIdResponse(ok=False, message="not found")

        return customer_pb2.GetCustomerByIdResponse(
            ok=True, message="ok", customer=dict_to_customer_msg(doc)
        )

    def UpdateCustomer(self, request, context):
        updates = build_update_dict(request.customer)
        if not updates:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("no fields provided to update")
            return customer_pb2.UpdateCustomerResponse(
                ok=False, message="no fields to update"
            )

        found = self.db.update_customer(request.customerid, updates)
        if not found:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("customer not found")
            return customer_pb2.UpdateCustomerResponse(ok=False, message="not found")

        return customer_pb2.UpdateCustomerResponse(ok=True, message="updated")

    def DeleteCustomer(self, request, context):
        deleted = self.db.delete_customer(request.customerid)
        if not deleted:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("customer not found")
            return customer_pb2.DeleteCustomerResponse(ok=False, message="not found")

        return customer_pb2.DeleteCustomerResponse(ok=True, message="deleted")


def serve():
    """
    Docstring for serve
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    customer_pb2_grpc.add_CustomerServiceServicer_to_server(CustomerService(), server)
    grpc_port = EnvConfig().grpc_port
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    print(f"✅ gRPC server running on :{grpc_port}")
    server.wait_for_termination()
