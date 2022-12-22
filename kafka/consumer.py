import datetime
from flask import Flask, Response
from confluent_kafka import Consumer

topic = "distributed-video1"

c = Consumer({
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'mygroup',
    'auto.offset.reset': 'earliest'
})

c.subscribe([topic])

app = Flask(__name__)


@app.route('/video', methods=['GET'])
def video():
    """
    This is the heart of our video display. Notice we set the mimetype to
    multipart/x-mixed-replace. This tells Flask to replace any old images with
    new values streaming through the pipeline.
    """
    return Response(
        get_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame')


def get_video_stream():
    """
    Here is where we recieve streamed images from the Kafka Server and convert
    them to a Flask-readable format.
    """
    msg = c.poll(1.0)
    yield (b'--frame\r\n'
           b'Content-Type: image/jpg\r\n\r\n' + msg.value() + b'\r\n\r\n')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
