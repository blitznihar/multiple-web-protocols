"""
Docstring for soap.__main__
"""

import sys
import collections.abc

from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from soap.customer_service import CustomerSoapService

# 1. Compatibility Shim for 'six' - Must be done BEFORE any spyne imports
try:
    import spyne.util.six.moves
except ImportError:
    from types import ModuleType

    m = ModuleType("spyne.util.six.moves")
    m.collections_abc = collections.abc
    sys.modules["spyne.util.six.moves"] = m
    sys.modules["spyne.util.six.moves.collections_abc"] = collections.abc

# 2. Strategic Import Order
# Import const first to ensure it's in sys.modules,
# then let spyne initialize properly.
import spyne.const
import spyne

# Explicitly link 'const' to the spyne module if it's missing
# (This solves the AttributeError you're seeing)
if not hasattr(spyne, "const"):
    spyne.const = spyne.const

# 3. Standard Spyne imports
from spyne import Application
from spyne.protocol.soap import Soap11
from config.envconfig import EnvConfig


config = EnvConfig()


def main():
    """
    Docstring for main
    """
    host_address = config.host_address
    host = config.host
    soap_port = config.soap_port
    # Application Factory
    soap_app = Application(
        [CustomerSoapService],
        tns="spyne.customers.soap",
        in_protocol=Soap11(validator="soft"),
        out_protocol=Soap11(),
    )
    print(f"Starting SOAP server.. at {host_address}:{soap_port}.")
    wsgi_app = WsgiApplication(soap_app)

    server = make_server(host_address, soap_port, wsgi_app)
    print(f"SOAP Server running on http://{host}:{soap_port}")
    print(f"WSDL available at: http://{host}:{soap_port}/?wsdl")
    server.serve_forever()


if __name__ == "__main__":
    main()
