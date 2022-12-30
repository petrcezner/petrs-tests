# Kafka *How to*:
1) create `*_jass.conf`  file with following schema:
    ```json lines
    KafkaServer {
        org.apache.kafka.common.security.plain.PlainLoginModule required
        username="username"
        password="username-secret"
        user_wl="username-secret";
    };
    Server {
      org.apache.kafka.common.security.plain.PlainLoginModule required
      username="username"
      password="username-secret"
      user_wl="username-secret";
    };
    Client {
      org.apache.kafka.common.security.plain.PlainLoginModule required
      username="username"
      password="username-secret";
    };
    ```
2) edit volume path in `docker-compose.yml` file
3) start the docker container using: `docker-compose up --build`
4) run `create_topic` script. This will create topics in kafka with desired number of partitions
5) run `producer` script. This will start producing content to the created topic
6) run `consumer_kafka` script. This will start web-app for content showcasing