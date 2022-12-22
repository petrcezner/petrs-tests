import datetime
from flask import Flask, Response, render_template
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

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(r'index.html')

@app.route('/video', methods=['GET'])
def video():
    return Response(
        get_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame')


def get_video_stream():
    while True:
        msg = consumer.poll(6.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpg\r\n\r\n' + msg.value() + b'\r\n\r\n')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
