import pprint
import random
import threading
from pprint import pformat
import time

from node_socket import UdpSocket
from util import get_logger

logger = get_logger('main')


class Order:
    RETREAT = 0
    ATTACK = 1


class General:

    def __init__(self, my_id: int, is_traitor: bool, my_port: int,
                 ports: list, node_socket: UdpSocket, city_port: int,
                 order=None, log_name=None):
        self.my_id = my_id
        self.ports = ports
        self.city_port = city_port
        self.node_socket = node_socket
        self.my_port = my_port
        self.is_traitor = is_traitor
        self.orders = []
        self.order = order

        if log_name is None:
            log_name = f'general{my_id}'
        self.logger = get_logger(log_name)

        self.general_port_dictionary = {}
        for i in range(0, 4):
            self.general_port_dictionary[i] = ports[i]
        self.logger.debug('self.general_port_dictionary: '
                          f'{pformat(self.general_port_dictionary)}')

        self.port_general_dictionary = {}
        for key, value in self.general_port_dictionary.items():
            self.port_general_dictionary[value] = key
        self.logger.debug(f'self.port_general_dictionary: '
                          f'{pprint.pformat(self.port_general_dictionary)}')

        if self.my_id > 0:
            self.logger.info(f'General {self.my_id} is running...')
        else:
            self.logger.info('Supreme general is running...')
        self.logger.debug(f'is_traitor: {self.is_traitor}')
        self.logger.debug(f'ports: {pformat(self.ports)}')
        self.logger.debug(f'my_port: {self.my_port}')
        self.logger.debug(f'is_supreme_general: {self.my_id == 0}')
        if self.order:
            self.logger.debug(f'order: {self.order}')
        self.logger.debug(f'city_port: {self.city_port}')

    def close_connection(self):
        self.node_socket.close()

    def start(self):

        """
        - Listen to all generals and distribute message to all your neighbor.

        :return: None
        """

        self.logger.info(f"General {self.my_id} is starting...")
        self.logger.info("Start listening for incoming messages...")

        time.sleep(3)
        for _ in range(3):
            msg = self.listen_procedure()
            self.sending_procedure(msg[0], int(msg[1].split("=")[1]))

        self.logger.info(f'Concluding action...')
        conclusion = self.conclude_action(self.orders)

        if self.is_traitor:
            action_message = "I am a traitor..."
        else:
            action = "RETREAT" if conclusion.split("=")[1] == "0" else "ATTACK"
            action_message = f"action: {action}\nDone doing my action..."

        self.logger.info(action_message)

    def listen_procedure(self):

        """
        - Receives a message

        :return: list of splitted message
        """

        msg = self.node_socket.listen()[0].split('~')

        self.logger.info(f'Got incoming message from {msg[0]}: {msg}')
        self.logger.info(f"Append message to a list: {self.orders}")

        order = int(msg[1].split("=")[1])
        self.orders.append(order)

        return msg

    def get_random_order(self):
        return random.choice([Order.ATTACK, Order.RETREAT])

    def sending_procedure(self, sender, order):
        """
        Sends message (order) to all your neighbor except the sender and the first port in your list.
        If the sender is the supreme general, sends the order to other generals using threading.
        If this node is a traitor, it may send a different order.

        :param sender: sender id
        :param order: order
        :return: list of sent messages
        """

        # Only proceed if the sender is the supreme general
        if sender != "supreme_general":
            return None

        self.logger.info("Send supreme general order to other generals with threading...")
        sent_messages = []
        for index, target_port in enumerate(self.ports):
            if index == 0 or target_port == self.my_port: continue

            final_order = str(
                self.get_random_order()) if self.is_traitor else order
            message = f"general_{self.my_id}~order={final_order}"

            self.logger.info(f"message: {message}")
            self.logger.info(f'Initiate threading to send the message...')
            self.logger.info(f'Start threading...')
            sent_messages.append(message)

            self.node_socket.send(message, target_port)
            self.logger.info(f"Done sending message to general {index}...")

        return sent_messages

    def _most_common(self, lst):
        return max(set(lst), key=lst.count)

    def conclude_action(self, orders):
        """
        Makes a conclusion based on received orders and sends the conclusion to the city as a form of consensus.

        :param orders: list of orders where 0 indicates retreat and any other value indicates attack
        :return: a conclusion message sent to the city
        """

        num_retreats = orders.count(0)
        num_attacks = len(orders) - num_retreats

        if self.is_traitor:
            return None

        action = 1 if num_attacks > num_retreats else 0
        conclusion_message = f"general_{self.my_id}~action={action}"
        self.node_socket.send(conclusion_message, self.city_port)

        return conclusion_message


class SupremeGeneral(General):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, log_name='supreme_general', **kwargs)

    def start(self):
        """
        - Do i need to listen to other generals?

        :return: None
        """
        self.logger.info("Supreme general is starting...")
        self.logger.info("Wait until all generals are running...")

        self.sending_procedure("supreme_general", self.order)
        self.logger.info("Concluding action...")

        # Conclude and send the final action based on consensus
        conclusion = self.conclude_action(self.orders)

        # for debugging
        if conclusion is not None:
            self.logger.debug(f"Action concluded and sent: {conclusion}")
        else:
            self.logger.debug("No conclusion reached (traitor mode).")

    def sending_procedure(self, sender, order):
        """
        - Sends order for every generals.

        :param sender: sender id
        :param order: order
        :return: list of sent orders
        """
        sent_orders = []
        for general_index in range(1, 4):
            time.sleep(1)
            final_order = self.get_random_order() if self.is_traitor else order
            message = f"{sender}~order={final_order}"
            sent_orders.append(final_order)
            self.node_socket.send(message, self.ports[general_index])
            self.logger.info(f"Send message to general {general_index} with port {self.ports[general_index]}")

        self.logger.info("Finished sending messages to other generals.")
        return sent_orders

    def conclude_action(self, orders):
        """
        - This means the logic to make a conclusion
        for supreme general is different.
        - Sends the conclusion to the city as a form of consensus.

        :param orders: list
        :return: str or None
        """

        if self.is_traitor:
            self.logger.info("I am a traitor...")
            return None

        action_description = "RETREAT from the city..." if self.order == 0 else "ATTACK the city..."
        self.logger.info(action_description)

        conclusion_message = f"supreme_general~action={self.order}"
        self.node_socket.send(conclusion_message, self.city_port)
        self.logger.info("Send information to city...")
        self.logger.info("Done sending information...")

        return conclusion_message


def thread_exception_handler(args):
    logger.error('Uncaught exception', exc_info=(args.exc_type,
                                                 args.exc_value,
                                                 args.exc_traceback))


def main(is_traitor: bool, node_id: int, ports: list,
         my_port: int = 0, order: Order = Order.RETREAT,
         city_port: int = 0):
    threading.excepthook = thread_exception_handler
    try:
        if node_id == 0:
            obj = SupremeGeneral(my_id=node_id,
                                 city_port=city_port,
                                 is_traitor=is_traitor,
                                 node_socket=UdpSocket(my_port),
                                 my_port=my_port,
                                 ports=ports, order=order)
        else:
            obj = General(my_id=node_id,
                          city_port=city_port,
                          is_traitor=is_traitor,
                          node_socket=UdpSocket(my_port),
                          my_port=my_port,
                          ports=ports)
        obj.start()
    except Exception:
        logger.exception('Caught Error')
        raise

    finally:
        obj.close_connection()
