"""
Code to create ECS/fargate tasks for creating/destroying instances
"""
import boto3
import logging
from decouple import config

CLUSTER_NAME = config("CLUSTER_NAME")
SEC_GROUP_ID = config("SECURITY_GROUP")
TASK_ARN = config("TASK_ARN")
SUBNETS = config("SUBNETS")

ecs = boto3.client("ecs")
logger = logging.getLogger(__name__)

def destroy_desktop_instance(desktop_id, ami_id, machine_username, screen_geometry, machine_def_id, instance_type, user_data):
  """
  Create a task to destroy an instance
  """
  environment = {
    "MODE": "destroy",
    "DESKTOP_ID": desktop_id,
    "AMI_ID": ami_id,
    "MACHINE_USERNAME": machine_username,
    "SCREEN_GEOMETRY": screen_geometry,
    "MACHINE_DEF_ID": machine_def_id,
    "INSTANCE_TYPE": instance_type,
    "B64_USER_DATA": user_data
  }
  return start_standalone_task(
    task_arn = TASK_ARN,
    cluster = CLUSTER_NAME,
    subnets = SUBNETS.split(","),
    security_group = SEC_GROUP_ID,
    environment = environment
  )

def create_desktop_instance(desktop_id, ami_id, machine_username, screen_geometry, machine_def_id, instance_type, user_data):
  """
  Create a task to create an instance
  """
  environment = {
    "MODE": "apply",
    "DESKTOP_ID": desktop_id,
    "AMI_ID": ami_id,
    "MACHINE_USERNAME": machine_username,
    "SCREEN_GEOMETRY": screen_geometry,
    "MACHINE_DEF_ID": machine_def_id,
    "INSTANCE_TYPE": instance_type,
    "B64_USER_DATA": user_data
  }
  return start_standalone_task(
    task_arn = TASK_ARN,
    cluster = CLUSTER_NAME,
    subnets = SUBNETS.split(","),
    security_group = SEC_GROUP_ID,
    environment = environment
  )

def start_standalone_task(task_arn, cluster, subnets, security_group, environment):
  """
  Start a standalone task
  """
  logger.info(f"Will use subnets: {subnets}")
  environmentOverrides = []
  for key, value in environment.items():
    environmentOverrides.append({
      "name": key,
      "value": value
    })
  params = {
    "cluster": cluster,
    "count": 1,
    "launchType": "FARGATE",
    "networkConfiguration": {
      "awsvpcConfiguration": {
        "subnets": subnets,
        "securityGroups": [ security_group ],
        "assignPublicIp": "DISABLED"
      }
    },
    "overrides": {
      "containerOverrides": [
        {
          "name": "instance-manager",
          "environment": environmentOverrides
        }
      ]
    },
    "taskDefinition": task_arn
  }
  logger.info(f"About to create this task {params}")
  response = ecs.run_task(**params)
  if len(response["tasks"]) > 0:
    logger.info("Task was created")
    return True
  else:
    logger.info("Task was not created")
    return False