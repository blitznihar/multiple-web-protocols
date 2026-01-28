"""GraphQL Service Main Module"""

from fastapi import FastAPI
import uvicorn
from strawberry.fastapi import GraphQLRouter
from .schema import schema
from config.envconfig import EnvConfig

app = FastAPI()
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


def main():
    """
    Docstring for graphql_service main
    """
    config = EnvConfig()
    host_address = config.host_address
    port = config.graphql_port
    print(f"Hello from graphql on {host_address}:{port}!")
    uvicorn.run(app, host=host_address, port=port)


if __name__ == "__main__":
    main()
