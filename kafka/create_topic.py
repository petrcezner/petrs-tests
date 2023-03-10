import logging

from confluent_kafka.admin import AdminClient, NewTopic

logger = logging.getLogger('topic_creator.py')

n_repicas = 1
n_partitions = 3
topic = "distributed-video1"

admin_client = AdminClient({
    "bootstrap.servers": "localhost:9093",
    'security.protocol': 'sasl_plaintext',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'wl',
    'sasl.password': 'wl-secret'
})

topic_list = [NewTopic(topic, n_partitions, n_repicas)]
fs = admin_client.create_topics(topic_list)

for topic, f in fs.items():
    try:
        f.result()
        logger.info(f"Topic {topic} created")
    except Exception as e:
        logger.warning(f"Failed to create topic {topic}: {e}")
