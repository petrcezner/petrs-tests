import asyncio
from pathlib import Path
from typing import Union
from xml.dom import minidom

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256


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


class QiOpcUa:
    def __init__(
        self,
        setup_xml: Union[str, Path],
        topics: dict,
        # publish_topic: dict,
        p2k: asyncio.Event,
        host_ip: str = "localhost",
        host_port: int = 4840,
        publishing_interval: int = 100,
    ):
        self.url = f"opc.tcp://{host_ip}:{host_port}"
        self.qi_node_id = get_nodeid_from_xml(setup_xml)
        self.client = Client(url=self.url)
        self.p2k = p2k
        self.topics = topics
        self.handlers = []
        # self.q = q
        self.publishing_interval = publishing_interval

    async def topic_subscriber(self, struct):
        callbacks = {f'{struct.nodeid.Identifier}."{topic}"': self.topics[topic] for topic in self.topics}
        self.variables = [self.client.get_node(f'{self.qi_node_id}."{topic}"') for topic in self.topics]
        handler = SubscriptionHandler(callbacks)
        self.subscription = await self.client.create_subscription(self.publishing_interval, handler)
        await self.subscription.subscribe_data_change(self.variables)

    async def delete_subscription(self):
        await self.subscription.delete()
        await asyncio.sleep(1)

    async def _set_variable(self, variable, value, dtype: ua.VariantType):
        print(variable)
        node = [var for var in self.variables if variable in var.nodeid.Identifier][0]
        print(node)
        await node.set_value(ua.DataValue(ua.Variant(value, dtype)))

    def set_variable(self, variable, value, dtype: ua.VariantType):
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self._set_variable(variable, value, dtype), loop=loop)
        loop.run_until_complete(asyncio.sleep(0.01))

    async def run(self) -> None:
        async with self.client:
            self.client.set_user("quiality")
            self.client.set_password("Sentics2016info!")
            await self.client.load_data_type_definitions()
            struct = self.client.get_node(self.qi_node_id)
            await self.topic_subscriber(struct)
            while not self.p2k.is_set():
                await asyncio.sleep(1)

    async def on_close(self):
        await self.delete_subscription()
        loop = asyncio.get_event_loop()
        loop.close()


if __name__ == "__main__":
    import logging

    def dummy_callback(node, val):
        print("Python: New data change event", node, val)

    def loop_exception_handler(loop, context):
        print(f"Crashing but its OK: {context}")

    logging.basicConfig(level=logging.WARN)
    p2k = asyncio.Event()
    qi_opc_ua = QiOpcUa(
        "data/opcua/QI.PLC_1.OPCUA.xml",
        {
            f"start_inference": dummy_callback,
            f"take_picture": dummy_callback,
            f"part_ok": dummy_callback,
        },
        p2k,
        host_ip="192.168.6.26",
    )
    # loop = asyncio.get_event_loop()
    # loop.set_exception_handler(loop_exception_handler)
    try:
        # loop.create_task(qi_opc_ua.run())
        # loop.run_forever()
        asyncio.run(qi_opc_ua.run())
        qi_opc_ua.set_variable("PartOK", False, ua.VariantType.Boolean)
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Loop")
        # loop.run_until_complete(qi_opc_ua.on_close())
        # loop.close()
