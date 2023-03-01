IP=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
xhost +
docker run --rm -it \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v ${PWD}:/mnt/data \
    -e DISPLAY=$IP:0 \
    -u qtuser \
    opcua-modeler:local
