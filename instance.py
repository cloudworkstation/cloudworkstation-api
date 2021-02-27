"""
Code to deal with EC2 instances
"""
import logging
import boto3

logger = logging.getLogger(__name__)

ec2 = boto3.client("ec2")

def start_instance(instanceid, hibernate = False):
  """
  Start and EC2 instance
  """
  response = ec2.start_instances(
    InstanceIds = [instanceid]
  )
  logging.info(f"Got response from EC2 api {response}")

def stop_instance(instanceid, hibernate = False):
  """
  Stop an EC2 instance
  """
  response = ec2.stop_instances(
    InstanceIds = [instanceid],
    Hibernate = hibernate
  )
  logging.info(f"Got response from EC2 api {response}")

def get_instances_by_username_and_id(username, instanceid):
  """
  Helper method to find an instance which belongs to a given user and which has a specific ID
  """
  instances = scan_for_instances_with_tags([
    {
      "name": "MachineType",
      "value": "Desktop"
    },
    {
      "name": "Username",
      "value": username
    },
    {
      "name": "DesktopId",
      "value": instanceid
    }
  ])
  return clean_up_instances(instances)


def get_instances_by_username(username):
  """
  Helper method to search for instances belonging to a given user
  """
  instances = scan_for_instances_with_tags([
    {
      "name": "MachineType",
      "value": "Desktop"
    },
    {
      "name": "Username",
      "value": username
    }
  ])
  return clean_up_instances(instances)

def clean_up_instances(instances):
  """
  Cleans the instance raw data up to send back to client
  """
  cleansed_instances = {}
  for instance in instances:
    cleansed_instances.update({
      instance["tags"]["DesktopId"]: {
        "instanceid": instance["instanceid"],
        "dns": instance["dns"],
        "launchtime": instance["launchtime"],
        "state": instance["state"],
        "screengeometry": instance["tags"]["ScreenGeometry"],
        "machine_def_id": instance["tags"]["MachineDef"]
      }
    })
  return cleansed_instances

def tag_list_to_dict(tags):
  """
  Takes a list of dicts and makes a single dict
  """
  new_tags = {}
  for tag in tags:
    new_tags.update({
      tag["Key"]: tag["Value"]
    })
  return new_tags

def scan_for_instances_with_tags(tags):
  """
  Scan for instances with specific tags
  Does not return terminated instances
  """
  custom_filter = [{
    "Name": "instance-state-name",
    "Values": ["stopped", "running", "pending", "shutting-down", "stopping"]
  }]
  for tag in tags:
    custom_filter.append({
      "Name":   "tag:{tag}".format(tag = tag["name"]),
      "Values": [tag["value"]]
    })
  response = ec2.describe_instances(Filters=custom_filter)
  instances = []
  if len(response["Reservations"]) > 0:
    for reservation in response["Reservations"]:
      if "Instances" in reservation:
        for instance in reservation["Instances"]:
          instances.append({
            "instanceid": instance["InstanceId"],
            "dns": instance["PrivateDnsName"],
            "launchtime": instance["LaunchTime"],
            "state": instance["State"]["Name"],
            "tags": tag_list_to_dict(instance["Tags"]),
            "securitygroups": instance["SecurityGroups"]
          })
  return instances