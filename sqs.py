"""
Code to manage communications with SQS and SNS
"""
import logging
import boto3
import json

from utils import get_rand_string

logger = logging.getLogger(__name__)
sqs = boto3.client("sqs")
sns = boto3.client("sns")

class SqsHandler(object):

  def __init__(self, topic_name, kms_id):
    """
    Create object
    """
    self.topic_name = topic_name
    self.kms_id = kms_id
    self.queue_url = ""
    self.sub_arn = ""

  def _get_queue_policy(queue_arn, topic_name):
    """
    Makes a policy to apply to an SQS queue
    """
    queue_policy = {
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "sns.amazonaws.com"
          },
          "Action": "sqs:SendMessage",
          "Resource": queue_arn,
          "Condition": {
            "ArnEquals": {
              "aws:SourceArn": topic_name
            }
          }
        }
      ]
    }
    return queue_policy

  def unsubscribe_and_delete_queue(self):
    """
    Deletes the queue and removes the associated subscription
    """
    logger.info("Deleting SQS queue and subscription")
    sns.unsubscribe(SubscriptionArn=self.sub_arn)
    sqs.delete_queue(QueueUrl=self.queue_url)

  def create_queue_and_subscribe(self):
    """
    Creates an SQS queue and subscribes it to the SNS topic with state change notifications
    """
    queue_rand = get_rand_string(8)
    queue = sqs.create_queue(
      QueueName=f"ec2_{queue_rand}",
      Attributes={
        "KmsMasterKeyId": self.kms_id
      }
    )
    queue_attr = sqs.get_queue_attributes(QueueUrl=queue["QueueUrl"], AttributeNames=["QueueArn"])
    queue_policy = SqsHandler._get_queue_policy(
      queue_arn = queue_attr["Attributes"]["QueueArn"],
      topic_name = self.topic_name
    )
    sqs.set_queue_attributes(
      QueueUrl=queue["QueueUrl"],
      Attributes={
        "Policy": json.dumps(queue_policy)
      }
    )
    sns_sub = sns.subscribe(
      TopicArn=self.topic_name,
      Protocol="SQS",
      Endpoint=queue_attr["Attributes"]["QueueArn"]
    )
    self.queue_url = queue["QueueUrl"]
    self.sub_arn = sns_sub["SubscriptionArn"]
    return queue["QueueUrl"]