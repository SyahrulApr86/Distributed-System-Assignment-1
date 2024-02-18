import threading

from node import Order
from node_socket import UdpSocket
from util import get_logger

logger = get_logger('main')


class City:

    def __init__(self, my_port: int, number_general: int) -> None:
        self.number_general = number_general
        self.my_port = my_port
        self.node_socket = UdpSocket(my_port)
        self.logger = get_logger('city')

        self.logger.debug(f'city_port: {self.my_port}')
        self.logger.info(f'City is running...')
        self.logger.info(f'Number of loyal general: {number_general}')

    def close_connection(self):
        self.node_socket.close()

    def start(self):
        order_counts = {Order.ATTACK: 0, Order.RETREAT: 0}
        received_messages = 0

        self.logger.info('Listen to incoming messages...')
        for _ in range(self.number_general):
            message, _ = self.node_socket.listen()
            if message:
                received_messages += 1
                sender, action_order = message.split('~')
                action, order_str = action_order.split('=')
                order = int(order_str)

                action_str = 'ATTACK' if order == Order.ATTACK else 'RETREAT'
                self.logger.info(f'{sender} {action_str} from us!')

                if order == Order.ATTACK:
                    order_counts[Order.ATTACK] += 1
                elif order == Order.RETREAT:
                    order_counts[Order.RETREAT] += 1

        if received_messages < 2:
            self.logger.error('ERROR_LESS_THAN_TWO_GENERALS')
            return 'ERROR_LESS_THAN_TWO_GENERALS'

        self.logger.info('Concluding what happen...')
        if order_counts[Order.ATTACK] > 0 and order_counts[Order.RETREAT] > 0:
            conclusion = 'FAILED'
        elif order_counts[Order.ATTACK] > order_counts[Order.RETREAT]:
            conclusion = 'ATTACK'
        else:
            conclusion = 'RETREAT'

        self.logger.info(f'GENERAL CONSENSUS: {conclusion}')
        return conclusion


def thread_exception_handler(args):
    logger.error('Uncaught exception', exc_info=(args.exc_type,
                                                 args.exc_value,
                                                 args.exc_traceback))


def main(city_port: int, number_general: int):
    threading.excepthook = thread_exception_handler
    try:
        city = City(city_port, number_general)
        return city.start()

    except Exception:
        logger.exception('Caught Error')
        raise

    finally:
        city.close_connection()
