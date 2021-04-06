import boto3

sqs = boto3.client("sqs")

def find_and_remove():
  response = sqs.list_queues(
    QueueNamePrefix="ec2_",
    MaxResults=100
  )
  if "QueueUrls" in response:
    for qurl in response["QueueUrls"]:
      print(f"Going to delete queue @ {qurl} ...")
      sqs.delete_queue(
        QueueUrl=qurl
      )
      print("...Deleted.")

if __name__ == "__main__":
  find_and_remove()