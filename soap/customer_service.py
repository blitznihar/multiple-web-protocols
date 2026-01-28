"""
Docstring for soap.soap_customer_service
"""

from spyne import rpc, ServiceBase, Unicode, Integer, Boolean, ComplexModel
from db.customer_db import CustomerDB

# ... your database and envconfig imports

# ... (Rest of your code)
from config.envconfig import EnvConfig


# Define the Data Model for SOAP
class Customer(ComplexModel):
    """
    Docstring for Customer
    """

    customerid = Unicode
    name = Unicode
    email = Unicode
    age = Integer


config = EnvConfig()


class CustomerSoapService(ServiceBase):
    """
    Docstring for CustomerSoapService
    """

    # Initialize the DB helper

    db = CustomerDB(
        uri=config.database_url,
        db_name=config.db_name,
        collection_name=config.collection_name,
    )

    @rpc(Unicode, Unicode, Unicode, Integer, _returns=Unicode)
    def create_customer(ctx, customerid, name, email, age):
        """
        Docstring for create_customer

        :param ctx: Description
        :param customerid: Description
        :param name: Description
        :param email: Description
        :param age: Description
        """
        cust_dict = {"customerid": customerid, "name": name, "email": email, "age": age}
        return ctx.descriptor.service_class.db.create_customer(cust_dict)

    @rpc(Unicode, _returns=Customer)
    def get_customer(ctx, customerid):
        """
        Docstring for get_customer

        :param ctx: Description
        :param customerid: Description
        """
        res = ctx.descriptor.service_class.db.get_customer_by_id(customerid)
        if res:
            return Customer(**res)
        return None

    @rpc(Unicode, Unicode, _returns=Boolean)
    def update_customer_email(ctx, customerid, new_email):
        """
        Docstring for update_customer_email

        :param ctx: Description
        :param customerid: Description
        :param new_email: Description
        """
        # Simplification for SOAP: updating specific field
        return ctx.descriptor.service_class.db.update_customer(
            customerid, {"email": new_email}
        )

    @rpc(Unicode, _returns=Boolean)
    def delete_customer(ctx, customerid):
        """
        Docstring for delete_customer

        :param ctx: Description
        :param customerid: Description
        """
        return ctx.descriptor.service_class.db.delete_customer(customerid)
