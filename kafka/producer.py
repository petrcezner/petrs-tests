import logging
import sys
import time
import cv2
from confluent_kafka import Producer
import simplejpeg

topic = "distributed-video1"

logger = logging.getLogger('producer.py')


def delivery_report(err, msg):
    if err is not None:
        logger.warning('Message delivery failed: {}'.format(err))
    else:
        logger.info('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


def publish_video(video_file):
    producer = Producer({'bootstrap.servers': 'localhost:29092'})
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
    producer = Producer({'bootstrap.servers': 'localhost:29092'})
    camera = cv2.VideoCapture(0)

    try:
        while True:
            success, frame = camera.read()
            ret, buffer = cv2.imencode('.jpg', frame)
            # jpg_buffer = simplejpeg.encode_jpeg(frame,
            #                                     quality=75,
            #                                     colorspace='BGR')
            producer.produce(topic, buffer, callback=delivery_report)
            time.sleep(0.001)
            producer.poll(0)
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
