import logging
from bson import json_util

import paho.mqtt.client as mqtt
import uuid

logger = logging.getLogger("qi-mqtt-module" + ".mqtt.py")


class MqttClient:
    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: str = None,
        password: str = None,
        topics: list = None,
        module_name: str = None,
        bind_address: str = "0.0.0.0",
        qos_default: int = 2,
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.bind_address = bind_address
        self.module_type = f"{module_name}_{uuid.uuid4()}"
        self._client = mqtt.Client(client_id=self.module_type)
        self._topics = topics
        self.qos_default = min(2, max(0, qos_default))  # allowed: 0, 1, 2
        if username is not None and password is not None:
            self._client.username_pw_set(username=username, password=password)

    def connect(self) -> None:
        self.__setup_connection()
        self.start()

    def start(self) -> None:
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def __setup_connection(self) -> None:
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self.on_disconnect
        self._client.connect(host=self.host, keepalive=60, port=self.port, bind_address=self.bind_address)

    def publish(self, topic: str, response: object, qos: int = -1) -> None:
        logger.debug(f"Publishing to topic: {topic} message: {response}")
        if qos == -1:
            qos = self.qos_default
        return self._client.publish(topic, json_util.dumps(response), qos=qos)

    def _on_connect(self, client, userdata, flags, rc) -> None:
        logger.warning(f"Client connected to host {self.host} on port: {self.port}")
        for topic in self._topics:
            if len(topic) > 1:
                self._client.message_callback_add(topic[0], topic[1])
        self._client.subscribe([(topic[0], 2) for topic in self._topics])

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.error("Unexpected disconnection.")

    def _on_error(self) -> None:
        logger.error(f"MQTT communication error.")
