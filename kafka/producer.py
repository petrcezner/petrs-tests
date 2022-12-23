import logging
import sys
import time
import cv2
from confluent_kafka import Producer
import simplejpeg

topic = "distributed-video1"

logger = logging.getLogger('producer.py')
config = {
    'bootstrap.servers': 'localhost:9092',
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 100,
    'max.in.flight.requests.per.connection': 5,
    'compression.type': 'snappy',
    'linger.ms': 5,
    'batch.num.messages': 32
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


def publish_video(video_file):
    video = cv2.VideoCapture(video_file)

    logger.info('Publishing video...')

    while (video.isOpened()):
        producer.poll(0)
        success, frame = video.read()
        if not success:
            logger.warning("bad read!")
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        producer.produce(topic, buffer.tobytes(), callback=delivery_report)
        time.sleep(0.01)
        producer.flush()
    video.release()
    producer.flush()
    logger.info('Publish complete')


def publish_camera():
    camera = cv2.VideoCapture(0)

    try:
        while True:
            success, frame = camera.read()
            # ret, buffer = cv2.imencode('.jpg', frame)
            buffer = simplejpeg.encode_jpeg(frame,
                                            quality=95,
                                            colorspace='BGR')
            producer.produce(topic, buffer, callback=delivery_report)
            producer.poll(0)
            time.sleep(0.001)
    except KeyboardInterrupt:
        camera.release()
        producer.flush()
        logger.info("Exiting.")
        sys.exit(1)
    producer.flush()
    camera.release()


if __name__ == '__main__':
    if (len(sys.argv) > 1):
        video_path = sys.argv[1]
        publish_video(video_path)
    else:
        print("Publishing feed!")
        publish_camera()
