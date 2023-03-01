import os
import time
from pathlib import Path
import logging
import queue
from threading import Thread, Event
from typing import Union
from xml.dom import minidom

from asyncua.sync import Client, ua

logger = logging.getLogger("sync_opcua.py")


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


class QiOpcUaPublisher:
    def __init__(
        self,
        setup_xml: Union[str, Path],
        topics: dict,
        host_ip: str = "localhost",
        host_port: int = 4840,
        publishing_interval: int = 100,
    ):
        super().__init__()
        self.url = f"opc.tcp://{host_ip}:{host_port}"
        self.qi_node_id = get_nodeid_from_xml(setup_xml)
        self.client = Client(url=self.url)
        self.topics = topics
        self.publishing_interval = publishing_interval
        self.client.connect()
        self.client.set_user(os.environ.get("OPCUA_USER"))
        self.client.set_password(os.environ.get("OPCUA_PASSWORD"))
        self.client.load_data_type_definitions()
        self.topic_subscriber()

    def set_variable(self, variable, value, dtype: ua.VariantType):
        node = [var for var in self.variables if variable in var.nodeid.Identifier][0]
        logger.info(f"{node}, {value}, {dtype}")
        node.set_value(ua.DataValue(ua.Variant(value, dtype)))

    def topic_subscriber(self):
        self.variables = [self.client.get_node(f'{self.qi_node_id}."{topic}"') for topic in self.topics]

    def disconnect(self):
        self.client.disconnect()


class QiOpcUa(Thread):
    def __init__(
        self,
        setup_xml: Union[str, Path],
        topics: dict,
        p2k: Event,
        queue: queue.Queue,
        host_ip: str = "localhost",
        host_port: int = 4840,
        publishing_interval: int = 100,
    ):
        super().__init__()
        self.url = f"opc.tcp://{host_ip}:{host_port}"
        self.qi_node_id = get_nodeid_from_xml(setup_xml)
        self.client = Client(url=self.url)
        self.p2k = p2k
        self.topics = topics
        self.q = queue
        self.timeout = 1.0 / 60
        self.handlers = []
        self.publishing_interval = publishing_interval

    def topic_subscriber(self, struct):
        callbacks = {f'{struct.nodeid.Identifier}."{topic}"': self.topics[topic] for topic in self.topics}
        self.variables = [self.client.get_node(f'{self.qi_node_id}."{topic}"') for topic in self.topics]
        handler = SubscriptionHandler(callbacks)
        self.subscription = self.client.create_subscription(self.publishing_interval, handler)
        self.subscription.subscribe_data_change(self.variables)

    def delete_subscription(self):
        self.subscription.delete()
        time.sleep(1)

    def _set_variable(self, variable, value, dtype: ua.VariantType):
        node = [var for var in self.variables if variable in var.nodeid.Identifier][0]
        logger.info(f"{node}, {value}, {dtype}")
        node.set_value(ua.DataValue(ua.Variant(value, dtype)))

    def set_variable(self, variable, value, dtype: ua.VariantType):
        self.q.put((self._set_variable, variable, value, dtype))

    def run(self) -> None:
        with self.client:
            self.client.set_user(os.environ.get("OPCUA_USER"))
            self.client.set_password(os.environ.get("OPCUA_PASSWORD"))
            self.client.load_data_type_definitions()
            struct = self.client.get_node(self.qi_node_id)
            self.topic_subscriber(struct)
            while not self.p2k.is_set():
                try:
                    function, args, kwargs = self.q.get(timeout=self.timeout)
                    print(function, args, kwargs)
                    function(*args, **kwargs)
                except queue.Empty:
                    self.idle()
            self.delete_subscription()

    def idle(self):
        pass


if __name__ == "__main__":

    def dummy_callback(node, val):
        print("Python: New data change event", node, val)

    os.environ["OPCUA_USER"] = "quiality"
    os.environ["OPCUA_PASSWORD"] = "Sentics2016info!"
    logging.basicConfig(level=logging.INFO)
    p2k = Event()
    q = queue.Queue()
    publisher = QiOpcUaPublisher(
        "data/opcua/QI.PLC_1.OPCUA.xml",
        {
            f"start_inference": dummy_callback,
            f"stop_inference": dummy_callback,
            f"take_picture": dummy_callback,
            f"part_ok": dummy_callback,
        },
        host_ip="192.168.6.26",
    )
    publisher.set_variable("start_inference", True, ua.VariantType.Boolean)
    # qi_opc_ua = QiOpcUa("data/opcua/QI.PLC_1.OPCUA.xml",
    #                     {f'start_inference': dummy_callback,
    #                      f'take_picture': dummy_callback,
    #                      f'part_ok': dummy_callback},
    #                     p2k=p2k,
    #                     host_ip="192.168.6.26",
    #                     queue=q)
    # try:
    #     qi_opc_ua.run()
    #     qi_opc_ua.set_variable('part_ok', False, ua.VariantType.Boolean)
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     qi_opc_ua.join()
    #     print("Closing Loop")
