""" """

from .customerpb import customer_pb2, customer_pb2_grpc  # type: ignore
import grpc


def run():
    """
    Docstring for run
    """
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = customer_pb2_grpc.CustomerServiceStub(channel)

        # CREATE
        c = customer_pb2.Customer(  # type: ignore[attr-defined]
            customerid="99999",
            firstname="Nihar",
            lastname="Malali",
            email="nihar@example.com",
            phone="+1-555-1111",
            address=customer_pb2.Address(
                street="1 Test St",
                city="McKinney",
                state="TX",
                zip="75071",
                country="USA",
            ),
        )
        print(stub.CreateCustomer(customer_pb2.CreateCustomerRequest(customer=c)))

        # GET
        print(
            stub.GetCustomerById(
                customer_pb2.GetCustomerByIdRequest(customerid="99999")
            )
        )

        # UPDATE (partial)
        patch = customer_pb2.Customer(phone="+1-555-2222")
        print(
            stub.UpdateCustomer(
                customer_pb2.UpdateCustomerRequest(customerid="99999", customer=patch)
            )
        )

        # DELETE
        print(
            stub.DeleteCustomer(customer_pb2.DeleteCustomerRequest(customerid="99999"))
        )


if __name__ == "__main__":
    run()
