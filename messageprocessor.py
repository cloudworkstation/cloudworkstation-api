"""
Code which processes messages on SQS topic and sends notifications to client
"""

import json
import boto3
import logging
import threading
import queue
from collections import defaultdict

from instance import get_tags_for_instance

logger = logging.getLogger(__name__)
sqs = boto3.client("sqs")

class MessageProcessor(threading.Thread):
  def __init__(self, queueurl):
    super(MessageProcessor, self).__init__()
    self.queues = defaultdict(list)
    self.tag_cache = {}
    self.queueurl = queueurl
    self.stoprequest = threading.Event()
  
  def listen(self, username):
    logger.info(f"Adding queue for {username}")
    q = queue.Queue(maxsize=5)
    self.queues[username].append(q)
    return q

  def run(self):
    while not self.stoprequest.isSet():
      logger.info("Starting long poll of sqs queue...")
      response = sqs.receive_message(
        QueueUrl=self.queueurl,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=20
      )
      logger.info("Back from long poll")
      if "Messages" in response:
        for message in response["Messages"]:
          body = message["Body"]
          recphwnd = message["ReceiptHandle"]
          body = json.loads(body)
          body = json.loads(body["Message"])
          logger.info(body)
          detail_type = body["detail-type"]
          if detail_type == "EC2 Instance State-change Notification":
            instance_id = body["detail"]["instance-id"]
            state = body["detail"]["state"]
            logger.info(f"EC2 instance state change message {instance_id} {state}")
            # check cache of tag data
            if instance_id not in self.tag_cache:
              new_tags = get_tags_for_instance(instance_id)
              logger.info(f"Got tags for instance {instance_id}")
              logger.info(f"Tags returned {new_tags}")
              if new_tags:
                logger.info(f"Storing tags in cache for instance {instance_id}")
                self.tag_cache[instance_id] = new_tags
            username = self.tag_cache[instance_id]["Username"]
            desktop_id = self.tag_cache[instance_id]["DesktopId"]
            logger.info(f"Instance {instance_id} username {username} desktop_id {desktop_id}")
            if username in self.queues:
              logger.info(f"User {username} as event listener registered...")
              for i in reversed(range(len(self.queues[username]))):
                try:
                  self.queues[username][i].put_nowait(json.dumps({
                    "desktop_id": desktop_id,
                    "state": state,
                    "instance_id": instance_id
                  }))
                except queue.Full:
                  del self.queues[username][i]
          sqs.delete_message(
            QueueUrl=self.queueurl,
            ReceiptHandle=recphwnd
          )
      else:
        logger.info("Got no messages during long poll")
  
  def join(self, timeout=None):
    self.stoprequest.set()
    super(MessageProcessor, self).join(timeout)
  
