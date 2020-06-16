import json
from time import sleep

MAX_MESSAGES_PER_REQUEST=10
MAX_LONG_POLLING_TIME=20
SLEEP_BETWEEN_REQUESTS=5


class SQSListener:
    """Listener for SQS queues."""

    def __init__(
        self,
        queue_url,
        client,
        max_messages_per_request=MAX_MESSAGES_PER_REQUEST,
        max_long_polling_time=MAX_LONG_POLLING_TIME,
        sleep_between_requests=SLEEP_BETWEEN_REQUESTS,
    ):
        self.queue_url = queue_url
        self.client = client

        self.max_messages_per_request = max_messages_per_request
        self.max_long_polling_time = max_long_polling_time
        self.sleep_between_requests = sleep_between_requests

        self.messages_marked_to_be_deleted = []

    def process_messages(self):
        """Entrypoint for sqs message processing."""

        sqs_messages = self.client.receive_message(
            QueueUrl=self.queue_url,
            AttributeNames=["SequenceNumber"],
            MaxNumberOfMessages=self.max_messages_per_request,
            MessageAttributeNames=["All"],
            WaitTimeSeconds=self.max_long_polling_time,
        )

        events = []
        if "Messages" in sqs_messages:
            for sqs_message in sqs_messages["Messages"]:
                self.mark_message_to_be_deleted(sqs_message)
                event = self.pbsc_format(sqs_message)
                events.append(event)

        return events

    def pbsc_format(self, sqs_message):
        """Converts payload to pbsc format.
           Args:
               sqs_message(dict): message to be converted.
        """

        body = json.loads(sqs_message["Body"])
        event = json.loads(body["Message"])
        return event

    def mark_message_to_be_deleted(self, sqs_message):
        current_messages_to_delete_queue_length = len(
            self.messages_marked_to_be_deleted
        )

        if current_messages_to_delete_queue_length == 10:
            self.delete_messages_marked_to_be_deleted()

        self.messages_marked_to_be_deleted.append(sqs_message)

    def delete_messages_marked_to_be_deleted(self):
        messages_to_delete_now = []

        for _ in range(10):
            if not self.messages_marked_to_be_deleted:
                break

            message = self.messages_marked_to_be_deleted.pop(0)
            messages_to_delete_now.append(
                {"Id": message["MessageId"], "ReceiptHandle": message["ReceiptHandle"]}
            )
        self.client.delete_message_batch(
            QueueUrl=self.queue_url, Entries=messages_to_delete_now
        )

    def listen(self):
        while True:
            events = self.process_messages()
            for event in events:
                yield event
            sleep(self.sleep_between_requests)
