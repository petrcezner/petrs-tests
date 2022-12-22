import cv2
import numpy as np
from confluent_kafka import Consumer

topic = "distributed-video1"

settings = {
    'bootstrap.servers': 'localhost:29092',
    "group.id": "my-work-group",
    "client.id": "my-work-client-1",
    "enable.auto.commit": False,
    "session.timeout.ms": 6000,
    "default.topic.config": {"auto.offset.reset": "largest"},
}
consumer = Consumer(settings)


def on_assign(a_consumer, partitions):
    # get offset tuple from the first partition
    last_offset = a_consumer.get_watermark_offsets(partitions[0])
    # position [1] being the last index
    partitions[0].offset = last_offset[1] - 1
    consumer.assign(partitions)


consumer.subscribe([topic], on_assign=on_assign)

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        img = cv2.imdecode(np.fromstring(msg.value(), np.uint8),
                           cv2.IMREAD_COLOR)

        cv2.imshow('img', img)
        cv2.waitKey(1)
except KeyboardInterrupt:
    consumer.close()
