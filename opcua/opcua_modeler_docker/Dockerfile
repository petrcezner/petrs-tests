ARG BASE_IMAGE=jozo/pyqt5
FROM ${BASE_IMAGE} as base

RUN apt-get update && apt-get install -y python3-pip
RUN apt-get install -y '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
RUN pip3 install opcua-modeler

#ENV QT_DEBUG_PLUGINS=1

ENTRYPOINT ["opcua-modeler"]
CMD [""]