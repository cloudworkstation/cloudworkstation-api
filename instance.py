"""
Code to deal with EC2 instances
"""
import logging
import boto3

logger = logging.getLogger(__name__)

ec2 = boto3.client("ec2")

def get_instances_by_username(username):
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
  """
  custom_filter = []
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

if __name__ == "__main__":
  i = scan_for_instances_with_tags([{
    "name": "aws:ec2launchtemplate:id",
    "value": "lt-03873ae44981f4115"
  }])
  print(i)