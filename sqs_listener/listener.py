import json
from time import sleep
from typing import Dict, List, Optional

import botocore  # type: ignore

MAX_MESSAGES_PER_REQUEST = 10
MAX_LONG_POLLING_TIME = 20
MAX_ENQUEUED_DELETE_MESSAGES = 10
SLEEP_BETWEEN_REQUESTS = 5

PBSCMessageFormat = Dict[str, str]


class SQSListener:
    """Listener for SQS queues."""

    def __init__(
        self,
        queue_url: str,
        client: "botocore.client.SQS",
        max_messages_per_request: int = MAX_MESSAGES_PER_REQUEST,
        max_long_polling_time: int = MAX_LONG_POLLING_TIME,
        sleep_between_requests: int = SLEEP_BETWEEN_REQUESTS,
    ):
        self.queue_url = queue_url
        self.client = client

        self.max_messages_per_request = max_messages_per_request
        self.max_long_polling_time = max_long_polling_time
        self.sleep_between_requests = sleep_between_requests

        self.messages_to_delete_queue: List = []

    def process_messages(self) -> List[Optional[PBSCMessageFormat]]:
        """Entrypoint for sqs message processing."""
        sqs_messages = self.client.receive_message(
            QueueUrl=self.queue_url,
            AttributeNames=["SequenceNumber"],
            MaxNumberOfMessages=self.max_messages_per_request,
            MessageAttributeNames=["All"],
            WaitTimeSeconds=self.max_long_polling_time,
        )

        events: List[Optional[PBSCMessageFormat]] = []
        if "Messages" in sqs_messages:
            for sqs_message in sqs_messages["Messages"]:
                self.enqueue_message_to_be_deleted(sqs_message)
                event = self.pbsc_format(sqs_message)
                events.append(event)

        return events

    def pbsc_format(self, sqs_message) -> PBSCMessageFormat:
        """Converts payload to pbsc format.
           Args:
               sqs_message(dict): message to be converted.
        """

        body = json.loads(sqs_message["Body"])
        event = json.loads(body["Message"])
        return event

    def enqueue_message_to_be_deleted(self, sqs_message) -> None:
        """Marks messages to be deleted. if the deletion
           queue reaches MAX_ENQUEUED_DELETE_MESSAGES, triggers
           delete process.

           Args: sqs_message(dict): message to be enqueued/deleted.
        """
        current_messages_to_delete_queue_length = len(self.messages_to_delete_queue)

        if current_messages_to_delete_queue_length == MAX_ENQUEUED_DELETE_MESSAGES:
            self.delete_enqueued_messages()

        self.messages_to_delete_queue.append(sqs_message)

    def delete_enqueued_messages(self) -> None:
        """Executes deletion of previously marked messages."""
        messages_to_delete_now = []
        for _ in range(MAX_ENQUEUED_DELETE_MESSAGES):
            if not self.messages_to_delete_queue:
                break

            message = self.messages_to_delete_queue.pop(0)
            messages_to_delete_now.append(
                {"Id": message["MessageId"], "ReceiptHandle": message["ReceiptHandle"]}
            )

        if messages_to_delete_now:
            self.client.delete_message_batch(
                QueueUrl=self.queue_url, Entries=messages_to_delete_now
            )

    def listen(self):  # pragma: no cover
        """Continuosly listens to messages and yelds pbsc-like events."""
        while True:
            events = self.process_messages()
            for event in events:
                yield event
            sleep(self.sleep_between_requests)
