from typing import Dict, List
from unittest import TestCase
from unittest.mock import Mock, patch

from sqs_listener import SQSListener

SQS_RESPONSE_MULTIPLE_MESSAGES: Dict = {
    "Messages": [
        {
            "MessageId": "examplmockesqs_d_boto3_responseeMessageID1",
            "ReceiptHandle": "ExampleReceiptHandle1",
            "Body": '{"Message" : "{\\"id\\": \\"001\\"}"}',
        },
        {
            "MessageId": "exampleMessageID2",
            "ReceiptHandle": "ExampleReceiptHandle2",
            "Body": '{"Message" : "{\\"id\\": \\"002\\"}"}',
        },
    ],
    "ResponseMetadata": {},
}
BOTO3_SQS_EXAMPLE_RESPONSE_NO_MESSAGES: Dict = {"ResponseMetadata": {}}


class SQSListenerTestCase(TestCase):
    def setUp(self):
        self.queue_url = "example.com"
        self.mock_client = Mock()

        self.sqs = SQSListener(queue_url=self.queue_url, client=self.mock_client)

    def test_instantiate_client(self):
        self.assertEqual(self.sqs.queue_url, self.queue_url)
        self.assertEqual(self.sqs.client, self.mock_client)

    def test_format_response(self):
        sqs_message = SQS_RESPONSE_MULTIPLE_MESSAGES["Messages"][0]

        expected_response = {"id": "001"}
        actual_response = self.sqs.pbsc_format(sqs_message)
        self.assertEqual(actual_response, expected_response)

    @patch("sqs_listener.listener.SQSListener.enqueue_message_to_be_deleted")
    def test_process_multiple_messages(self, mocked_enqueue_message_to_be_deleted):
        self.mock_client.receive_message.return_value = SQS_RESPONSE_MULTIPLE_MESSAGES

        expected_response = [{"id": "001"}, {"id": "002"}]
        actual_response = self.sqs.process_messages()
        self.assertEqual(expected_response, actual_response)

        self.assertEqual(mocked_enqueue_message_to_be_deleted.call_count, 2)
        mock_calls = [
            x[1] for x in mocked_enqueue_message_to_be_deleted._mock_mock_calls
        ]
        self.assertEqual(
            mock_calls[0][0], SQS_RESPONSE_MULTIPLE_MESSAGES["Messages"][0]
        )
        self.assertEqual(
            mock_calls[1][0], SQS_RESPONSE_MULTIPLE_MESSAGES["Messages"][1]
        )

    def test_process_no_message(self):
        self.mock_client.receive_message.return_value = (
            BOTO3_SQS_EXAMPLE_RESPONSE_NO_MESSAGES
        )

        expected_response: List[None] = []
        actual_response = self.sqs.process_messages()
        self.assertEqual(expected_response, actual_response)

    @patch("sqs_listener.listener.SQSListener.delete_enqueued_messages")
    def test_enqueue_message_to_be_deleted_less_than_10(
        self, mocked_delete_enqueued_messages
    ):
        sqs_message = SQS_RESPONSE_MULTIPLE_MESSAGES["Messages"][0]

        self.sqs.enqueue_message_to_be_deleted(sqs_message)

        self.assertEqual(self.sqs.messages_to_delete_queue, [sqs_message])
        mocked_delete_enqueued_messages.assert_not_called()

    @patch("sqs_listener.listener.SQSListener.delete_enqueued_messages")
    def test_enqueue_message_to_be_deleted_more_than_10(
        self, mocked_delete_enqueued_messages
    ):
        self.sqs.messages_to_delete_queue = [{"Id": x} for x in range(10)]

        sqs_message = SQS_RESPONSE_MULTIPLE_MESSAGES["Messages"][0]
        self.sqs.enqueue_message_to_be_deleted(sqs_message)

        self.assertIn(sqs_message, self.sqs.messages_to_delete_queue)
        mocked_delete_enqueued_messages.assert_called_once_with()

    def test_delete_enqueued_messages_with_10_items(self):
        fakes_messages = [
            {"MessageId": x, "ReceiptHandle": f"ReceiptHandle{x}"} for x in range(10)
        ]
        self.sqs.messages_to_delete_queue = fakes_messages

        self.sqs.delete_enqueued_messages()

        self.mock_client.delete_message_batch.assert_called_once_with(
            Entries=[
                {"Id": 0, "ReceiptHandle": "ReceiptHandle0"},
                {"Id": 1, "ReceiptHandle": "ReceiptHandle1"},
                {"Id": 2, "ReceiptHandle": "ReceiptHandle2"},
                {"Id": 3, "ReceiptHandle": "ReceiptHandle3"},
                {"Id": 4, "ReceiptHandle": "ReceiptHandle4"},
                {"Id": 5, "ReceiptHandle": "ReceiptHandle5"},
                {"Id": 6, "ReceiptHandle": "ReceiptHandle6"},
                {"Id": 7, "ReceiptHandle": "ReceiptHandle7"},
                {"Id": 8, "ReceiptHandle": "ReceiptHandle8"},
                {"Id": 9, "ReceiptHandle": "ReceiptHandle9"},
            ],
            QueueUrl="example.com",
        )
        self.assertEqual(self.sqs.messages_to_delete_queue, [])

    def test_delete_enqueued_messages_less_than_10_items(self):
        fakes_messages = [
            {"MessageId": x, "ReceiptHandle": f"ReceiptHandle{x}"} for x in range(5)
        ]
        self.sqs.messages_to_delete_queue = fakes_messages

        self.sqs.delete_enqueued_messages()

        self.mock_client.delete_message_batch.assert_called_once_with(
            Entries=[
                {"Id": 0, "ReceiptHandle": "ReceiptHandle0"},
                {"Id": 1, "ReceiptHandle": "ReceiptHandle1"},
                {"Id": 2, "ReceiptHandle": "ReceiptHandle2"},
                {"Id": 3, "ReceiptHandle": "ReceiptHandle3"},
                {"Id": 4, "ReceiptHandle": "ReceiptHandle4"},
            ],
            QueueUrl="example.com",
        )
        self.assertEqual(self.sqs.messages_to_delete_queue, [])

    def test_delete_enqueued_messages_more_than_10_items(self):
        fakes_messages = [
            {"MessageId": x, "ReceiptHandle": f"ReceiptHandle{x}"} for x in range(20)
        ]
        self.sqs.messages_to_delete_queue = fakes_messages

        self.sqs.delete_enqueued_messages()

        self.mock_client.delete_message_batch.assert_called_once_with(
            Entries=[
                {"Id": 0, "ReceiptHandle": "ReceiptHandle0"},
                {"Id": 1, "ReceiptHandle": "ReceiptHandle1"},
                {"Id": 2, "ReceiptHandle": "ReceiptHandle2"},
                {"Id": 3, "ReceiptHandle": "ReceiptHandle3"},
                {"Id": 4, "ReceiptHandle": "ReceiptHandle4"},
                {"Id": 5, "ReceiptHandle": "ReceiptHandle5"},
                {"Id": 6, "ReceiptHandle": "ReceiptHandle6"},
                {"Id": 7, "ReceiptHandle": "ReceiptHandle7"},
                {"Id": 8, "ReceiptHandle": "ReceiptHandle8"},
                {"Id": 9, "ReceiptHandle": "ReceiptHandle9"},
            ],
            QueueUrl="example.com",
        )
        self.assertEqual(
            self.sqs.messages_to_delete_queue,
            [
                {"MessageId": 10, "ReceiptHandle": "ReceiptHandle10"},
                {"MessageId": 11, "ReceiptHandle": "ReceiptHandle11"},
                {"MessageId": 12, "ReceiptHandle": "ReceiptHandle12"},
                {"MessageId": 13, "ReceiptHandle": "ReceiptHandle13"},
                {"MessageId": 14, "ReceiptHandle": "ReceiptHandle14"},
                {"MessageId": 15, "ReceiptHandle": "ReceiptHandle15"},
                {"MessageId": 16, "ReceiptHandle": "ReceiptHandle16"},
                {"MessageId": 17, "ReceiptHandle": "ReceiptHandle17"},
                {"MessageId": 18, "ReceiptHandle": "ReceiptHandle18"},
                {"MessageId": 19, "ReceiptHandle": "ReceiptHandle19"},
            ],
        )

    def test_delete_enqueued_messages_no_messages_to_delete(self):
        self.sqs.messages_to_delete_queue = []

        self.sqs.delete_enqueued_messages()

        self.mock_client.delete_message_batch.assert_not_called()
