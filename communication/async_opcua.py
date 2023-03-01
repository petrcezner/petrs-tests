import sys
import asyncio
from functools import wraps
from pathlib import Path
from typing import Union, Callable
from xml.dom import minidom

import logging

from asyncua import Client, ua

# from asyncua.sync import Client, ua


def dummy_callback(node, val):
    print("Python: New data change event", node, val)


class SubscriptionHandler:
    def __init__(self, nodes_callback: dict):
        self.nodes_callback = nodes_callback

    def datachange_notification(self, node, val, data):
        self.nodes_callback[node.nodeid.Identifier](node, val)


def get_nodeid_from_xml(
    xml_file: Union[str, Path],
    brows_name: str = "QualityInspector",
    d_type: str = "QualityInspector",
):
    dom = minidom.parse(xml_file)
    elements = dom.getElementsByTagName("UAVariable")
    qi_tag = [
        element
        for element in elements
        if brows_name in element.attributes["BrowseName"].value
        and f'DT_"{d_type}"' in element.attributes["DataType"].value
    ]
    if len(qi_tag) > 1:
        raise ValueError("There are more then one ")
    return qi_tag[0].attributes["NodeId"].value


async def main():
    url = "opc.tcp://10.117.156.170:4840"
    qi_node_id = get_nodeid_from_xml("data/QI.PLC_1.OPCUA.xml")
    async with Client(url=url) as client:
        print("Root children are", await client.nodes.root.get_children())
        struct = client.get_node(qi_node_id)
        await client.load_data_type_definitions()  # scan server for custom structures and import them
        after = await struct.read_value()
        print("AFTER", after)
        var = client.get_node(f'{qi_node_id}."StartInfernce"')

        handler = SubscriptionHandler({f'{struct.nodeid.Identifier}."StartInfernce"': dummy_callback})
        # We create a Client Subscription.
        subscription = await client.create_subscription(500, handler)
        # We subscribe to data changes for two nodes (variables).
        await subscription.subscribe_data_change(var)
        # We let the subscription run for ten seconds
        await asyncio.sleep(700)
        # We delete the subscription (this un-subscribes from the data changes of the two variables).
        # This is optional since closing the connection will also delete all subscriptions.
        # await var.write_value(True)
        await subscription.delete()
        # After one second we exit the Client context manager - this will close the connection.
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main())
