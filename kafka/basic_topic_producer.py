import json
import logging
import sys
import time

from bson import json_util
from confluent_kafka import Producer

logger = logging.getLogger('producer.py')
config = {
    'bootstrap.servers': 'localhost:9093',
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 100,
    'max.in.flight.requests.per.connection': 5,
    'compression.type': 'snappy',
    'linger.ms': 5,
    'batch.num.messages': 32,
    'security.protocol': 'sasl_plaintext',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'wl',
    'sasl.password': 'wl-secret'
}
producer = Producer(config)


def delivery_report(err, msg):
    if err:
        logger.error(f"Failed to deliver message: {msg.value()}: {err.str()}")
    else:
        logger.info(f"msg produced. \n"
                    f"Topic: {msg.topic()} \n" +
                    f"Partition: {msg.partition()} \n" +
                    f"Offset: {msg.offset()} \n" +
                    f"Timestamp: {msg.timestamp()} \n")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    topic = "start_inference"
    producer.produce(topic, None, callback=delivery_report)
    producer.poll(0)
    producer.flush()
