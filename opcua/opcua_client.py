import logging
import asyncio

from asyncua import Client, ua, Node

_logger = logging.getLogger(__name__)


class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription
    This class is just a sample class. Whatever class having these methods can be used
    """

    def datachange_notification(self, node: Node, val, data):
        """
        called for every datachange notification from server
        """
        _logger.info("datachange_notification %r %s", node, val)

    def event_notification(self, event: ua.EventNotificationList):
        """
        called for every event notification from server
        """
        pass

    def status_change_notification(self, status: ua.StatusChangeNotification):
        """
        called for every status change notification from server
        """
        _logger.info("status_notification %s", status)


async def main():
    handler = SubHandler()

    while True:
        client = Client(url="opc.tcp://localhost:4840/freeopcua/server/")
        # client = Client(url="opc.tcp://localhost:53530/OPCUA/SimulationServer/")
        try:
            async with client:
                _logger.warning("Connected")
                idx = await client.get_namespace_index(uri="http://petrcezner.com/tests")
                var = await client.nodes.objects.get_child([f"{idx}:MyObject", f"{idx}:MyVariable"])
                handler = SubHandler()
                subscription = await client.create_subscription(500, handler)
                nodes = [
                    var,
                    client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
                ]
                await subscription.subscribe_data_change(nodes)
                while True:
                    await asyncio.sleep(1)
                    await client.check_connection()  # Throws a exception if connection is lost
        except (ConnectionError, ua.UaError):
            _logger.warning("Reconnecting in 2 seconds")
            await asyncio.sleep(2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
