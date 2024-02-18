from unittest import TestCase
from unittest.mock import patch, MagicMock

from city import City
from main import execution
from node import General, Order, SupremeGeneral

class BgpTest(TestCase):

    def setUp(self):
        self.patch_loggers = [patch('node.get_logger'), patch('city.logger'),
                              patch('city.get_logger')]
        [patch.start() for patch in self.patch_loggers]

        self.mock_udp = MagicMock()
        self.loyal_general = General(
            my_id=1,is_traitor=False,
            my_port=1,ports=[0,1,2,3],
            node_socket=self.mock_udp,
            city_port=4
        )
        self.loyal_supreme_general = SupremeGeneral(
            my_id=3, is_traitor=False,
            my_port=0, ports=[0,1,2,3],
            node_socket=self.mock_udp,
            city_port=4,
            order=Order.ATTACK
        )

        with patch('city.UdpSocket') as city_udp:
            self.mock_city_udp = city_udp()
            self.city = City(
                my_port=4,
                number_general=4
            )
        return super().setUp()

    def tearDown(self):
        [patch.stop() for patch in self.patch_loggers]
        return super().tearDown()

class BgpPublicTest(BgpTest):

    def test_listen_procedure_called_udpsocket_listen_once(self):
        self.mock_udp.listen.return_value = ('general_1~order=0',
                                             ('localhost', 123))
        self.loyal_general.listen_procedure()
        self.assertEqual(1,
                         self.mock_udp.listen.call_count)

    def test_listen_procedure_return_list(self):
        self.mock_udp.listen.return_value = ('general_1~order=0',
                                             ('localhost', 123))
        result = self.loyal_general.listen_procedure()
        self.assertEqual(result,
                         ['general_1', 'order=0'])

    def test_send_procedure_called_send_message_twice(self):
        self.loyal_general.sending_procedure('supreme_general', Order.ATTACK)
        self.assertEqual(2, self.mock_udp.send.call_count)

    def test_send_procedure_not_supreme_general_return_none(self):
        result = self.loyal_general.sending_procedure('general_1', Order.ATTACK)
        self.assertEqual(None, result)

    def test_send_procedure_return_message(self):
        order = Order.ATTACK
        result = self.loyal_general.sending_procedure('supreme_general', order)
        expected = f'general_{self.loyal_general.my_id}~order={order}'
        self.assertEqual([expected]*2, result)

    def test_concluding_action_called_send_message_once(self):
        self.loyal_general.conclude_action([Order.ATTACK, Order.RETREAT])
        self.assertEqual(1, self.mock_udp.send.call_count)

    def test_concluding_action_equal(self):
        result = self.loyal_general.conclude_action([Order.ATTACK,
                                                     Order.RETREAT])
        expected = f'general_{self.loyal_general.my_id}~action={Order.RETREAT}'
        self.assertEqual(result, expected)

    def test_concluding_action_return_message(self):
        result = self.loyal_general.conclude_action([Order.ATTACK,
                                                     Order.RETREAT,
                                                     Order.ATTACK])
        expected = f'general_{self.loyal_general.my_id}~action={Order.ATTACK}'
        self.assertEqual(result, expected)

    @patch('node.General.conclude_action')
    @patch('node.General.listen_procedure')
    @patch('node.General.sending_procedure')
    def test_start_method_called_all_procedure(self, mock_send, mock_listen,
                                               mock_conclude):
        self.loyal_general.start()
        self.assertEqual(3, mock_send.call_count)
        self.assertEqual(3, mock_listen.call_count)
        self.assertEqual(1, mock_conclude.call_count)

    def test_supreme_general_send_message_to_other_generals(self):
        self.loyal_supreme_general.sending_procedure(
            'supreme_general',
            self.loyal_supreme_general.order
        )
        self.assertEqual(3, self.mock_udp.send.call_count)

    def test_supreme_general_send_message_return_list(self):
        result = self.loyal_supreme_general.sending_procedure(
            'supreme_general',
            self.loyal_supreme_general.order
        )
        expected = [self.loyal_supreme_general.order for i in range(3)]
        self.assertEqual(expected, result)

    def test_supreme_general_send_information_to_city_once(self):
        self.loyal_supreme_general.conclude_action([])
        self.mock_udp.send.assert_called_once()

    def test_supreme_general_send_message_return_correct_format(self):
        result = self.loyal_supreme_general.conclude_action([])
        expected = f'supreme_general~action={self.loyal_supreme_general.order}'
        self.assertEqual(expected, result)

    @patch('node.SupremeGeneral.conclude_action')
    @patch('node.SupremeGeneral.sending_procedure')
    def test_supreme_general_called_all_procedures(self, mock_send,
                                                   mock_conclude):
        self.loyal_supreme_general.start()

        self.assertEqual(1, mock_send.call_count)
        self.assertEqual(1, mock_conclude.call_count)

    def test_city_listen_according_number_general(self):
        self.mock_city_udp.listen.side_effect = [
            ('general_1~order=0', ('localhost', 123)),
            ('supreme_general~order=0', ('localhost', 123)),
            ('general_2~order=0', ('localhost', 123)),
            ('general_3~order=0', ('localhost', 123)),
        ]
        self.city.start()
        self.assertEqual(self.city.number_general,
                         self.mock_city_udp.listen.call_count)

    def test_city_no_consensus(self):
        self.mock_city_udp.listen.side_effect = [
            ('general_1~order=1', ('localhost', 123)),
            ('supreme_general~order=0', ('localhost', 123)),
            ('general_2~order=1', ('localhost', 123)),
            ('general_3~order=0', ('localhost', 123)),
        ]
        result = self.city.start()
        expected = 'FAILED'
        self.assertEqual(expected, result)


class BgpPublicGrader(TestCase):

    def setUp(self):
        self.patch_loggers = [patch('main.logger'),patch('node.logger'),
                              patch('node.get_logger'),patch('city.logger'),
                              patch('city.get_logger')]
        [patch.start() for patch in self.patch_loggers]
        return super().setUp()

    def tearDown(self):
        [patch.stop() for patch in self.patch_loggers]
        return super().tearDown()

    @patch('node.General.get_random_order')
    def test_one_traitor_retreat_return_retreat(self, mock_random_order):
        mock_random_order.side_effect = [Order.ATTACK, Order.ATTACK]

        result = execution([False, True, False, False], 'RETREAT')
        expected = 'RETREAT'
        self.assertEqual(expected, result)

    @patch('node.SupremeGeneral.get_random_order')
    def test_supreme_traitor_attack_return_attack(self, mock_random_order):
        mock_random_order.side_effect = [Order.ATTACK, Order.ATTACK,
                                          Order.RETREAT]

        result = execution([True, False, False, False], 'ATTACK')
        expected = 'ATTACK'
        self.assertEqual(expected, result)

    @patch('node.General.get_random_order')
    def test_one_loyal_retreat_return_error(self, mock_random_order):
        mock_random_order.side_effect = [Order.ATTACK, Order.RETREAT,
                                          Order.RETREAT]

        result = execution([True, True, True, False], 'RETREAT')
        expected = 'ERROR_LESS_THAN_TWO_GENERALS'
        self.assertEqual(expected, result)

    @patch('node.General.get_random_order')
    @patch('node.SupremeGeneral.get_random_order')
    def test_two_traitors_attack_return_fail(self,
                                             mock_random_choice_sup,
                                             mock_random_choice_gen):
        mock_random_choice_sup.side_effect = [Order.ATTACK, Order.ATTACK,
                                              Order.RETREAT]
        mock_random_choice_gen.side_effect = [Order.RETREAT, Order.ATTACK]

        result = execution([True, False, True, False], 'ATTACK')
        expected = 'FAILED'
        self.assertEqual(expected, result)
