import strawberry
from typing import List, Optional
from db.customer_db import CustomerDB
from config.envconfig import EnvConfig

# Import your existing Pydantic models
from db.customer import Customer
from db.address import Address


@strawberry.experimental.pydantic.type(model=Address, all_fields=True)
class AddressType:
    pass


@strawberry.experimental.pydantic.type(model=Customer, all_fields=True)
class CustomerType:
    pass


@strawberry.type
class Query:
    @strawberry.field
    def get_customer(self, customerid: str) -> Optional[CustomerType]:
        config = EnvConfig()
        db = CustomerDB(config.database_url, config.db_name, config.collection_name)
        data = db.get_customer_by_id(customerid)
        db.close()

        if data:
            # 1. Cast the MongoDB dict to a Pydantic model
            # 2. Convert that Pydantic model to a Strawberry Type
            return CustomerType.from_pydantic(Customer(**data))
        return None

    @strawberry.field
    def list_customers(self) -> List[CustomerType]:
        config = EnvConfig()
        db = CustomerDB(config.database_url, config.db_name, config.collection_name)
        customers_data = db.list_customers()
        db.close()

        # Convert each dictionary to a Strawberry Type via Pydantic
        return [CustomerType.from_pydantic(Customer(**c)) for c in customers_data]


schema = strawberry.Schema(query=Query)
